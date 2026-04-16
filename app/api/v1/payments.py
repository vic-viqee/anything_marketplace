from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, Payment, PaymentStatus, Product, ProductStatus
from app.services.payment_service import fluxpay_client, FluxPayError

router = APIRouter(prefix="/payments", tags=["payments"])


class InitiatePaymentRequest(BaseModel):
    product_id: int
    phone_number: str


class PaymentResponse(BaseModel):
    id: int
    amount: int
    status: str
    fluxpay_checkout_request_id: str | None
    created_at: str


@router.post("/initiate")
async def initiate_payment(
    request: InitiatePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate M-Pesa payment for a product"""

    # Get product
    product = db.query(Product).filter(Product.id == request.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    if product.status != ProductStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not available",
        )

    if product.seller_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot buy your own product",
        )

    # Format phone number
    phone = request.phone_number.replace("+", "").replace(" ", "")
    if not phone.startswith("254"):
        phone = "254" + phone[-9:]

    try:
        # Create pending payment record
        payment = Payment(
            user_id=current_user.id,
            product_id=product.id,
            amount=product.price,
            status=PaymentStatus.PENDING,
            reference=f"ORDER-{product.id}-{current_user.id}",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        # Initiate payment with FluxPay
        result = await fluxpay_client.initiate_payment(
            amount=product.price,
            phone_number=phone,
            reference=f"ORDER-{payment.id}",
        )

        # Update payment with checkout request ID
        payment.fluxpay_checkout_request_id = result.get("checkout_request_id")
        db.commit()

        return {
            "success": True,
            "payment_id": payment.id,
            "checkout_request_id": result.get("checkout_request_id"),
            "amount": product.price,
            "message": "STK push sent to your phone. Enter PIN to confirm.",
        }

    except FluxPayError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment service error: {e.message}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/{payment_id}")
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get payment details and status"""

    payment = (
        db.query(Payment)
        .filter(
            Payment.id == payment_id,
            Payment.user_id == current_user.id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    # Check status with FluxPay if still pending
    if payment.status == PaymentStatus.PENDING and payment.fluxpay_checkout_request_id:
        try:
            fluxpay_status = await fluxpay_client.check_payment_status(
                payment.fluxpay_checkout_request_id
            )
            db_status = fluxpay_status.get("status", "").upper()

            if db_status == "SUCCESS":
                payment.status = PaymentStatus.SUCCESS
                db.commit()
            elif db_status == "FAILED":
                payment.status = PaymentStatus.FAILED
                db.commit()
        except Exception:
            pass

    return {
        "id": payment.id,
        "amount": payment.amount,
        "status": payment.status.value,
        "fluxpay_checkout_request_id": payment.fluxpay_checkout_request_id,
        "mpesa_receipt_no": payment.mpesa_receipt_no,
        "created_at": payment.created_at.isoformat() if payment.created_at else None,
    }


@router.post("/check/{checkout_request_id}")
async def check_payment_status(
    checkout_request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check payment status"""

    payment = (
        db.query(Payment)
        .filter(
            Payment.fluxpay_checkout_request_id == checkout_request_id,
            Payment.user_id == current_user.id,
        )
        .first()
    )

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        )

    if payment.status == PaymentStatus.PENDING:
        try:
            fluxpay_status = await fluxpay_client.check_payment_status(
                checkout_request_id
            )
            db_status = fluxpay_status.get("status", "").upper()

            if db_status == "SUCCESS":
                payment.status = PaymentStatus.SUCCESS
                payment.mpesa_receipt_no = fluxpay_status.get("mpesaReceiptNo")
                db.commit()
            elif db_status == "FAILED":
                payment.status = PaymentStatus.FAILED
                db.commit()
        except Exception:
            pass

    return {
        "status": payment.status.value,
        "checkout_request_id": checkout_request_id,
    }
