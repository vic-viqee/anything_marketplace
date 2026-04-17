from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.core.config import get_settings
from app.models.models import Payment, PaymentStatus, Product, ProductStatus, User
from app.services.payment_service import fluxpay_client
import hmac
import hashlib

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
settings = get_settings()


class FluxPayWebhookPayload(BaseModel):
    event: str
    timestamp: str
    data: dict


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature from FluxPay"""
    if not signature or not secret:
        return False
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


@router.post("/fluxpay")
async def fluxpay_webhook(
    request: Request,
    x_webhook_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    """Handle webhook from FluxPay payment service"""

    raw_body = await request.body()
    body = raw_body.decode()
    payload_json = await request.json()

    # Fix 1: Verify webhook signature (only if secret is configured)
    if settings.FLUXPAY_WEBHOOK_SECRET:
        if not verify_webhook_signature(
            body, x_webhook_signature, settings.FLUXPAY_WEBHOOK_SECRET
        ):
            print(f"Invalid webhook signature: {x_webhook_signature}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        print(
            "WARNING: FLUXPAY_WEBHOOK_SECRET not configured - skipping signature verification"
        )

    event = payload_json.get("event")
    data = payload_json.get("data", {})

    checkout_request_id = data.get("checkoutRequestId") or data.get(
        "checkout_request_id"
    )
    payment_status = data.get("status", "").upper()
    received_amount = data.get("amount")

    if not checkout_request_id:
        return {"message": "No checkout request ID"}

    # Fix 2: Idempotency - check if already processed
    existing_payment = (
        db.query(Payment)
        .filter(Payment.fluxpay_checkout_request_id == checkout_request_id)
        .first()
    )

    if existing_payment and existing_payment.status == PaymentStatus.SUCCESS:
        print(
            f"Payment already processed for checkout_request_id: {checkout_request_id}"
        )
        return {"message": "Payment already processed", "status": "success"}

    # Find payment by checkout request ID
    payment = existing_payment

    if not payment:
        print(f"Payment not found for checkout_request_id: {checkout_request_id}")
        return {"message": "Payment not found"}

    # Fix 3: Verify payment amount matches expected
    if received_amount and payment.amount:
        if int(received_amount) != int(payment.amount):
            print(f"Amount mismatch: expected {payment.amount}, got {received_amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount mismatch",
            )

    if event == "payment.success":
        payment.status = PaymentStatus.SUCCESS
        payment.mpesa_receipt_no = data.get("mpesaReceiptNo") or data.get(
            "mpesa_receipt_no"
        )
        db.commit()

        # Mark product as sold
        if payment.product_id:
            product = db.query(Product).filter(Product.id == payment.product_id).first()
            if product and product.status == ProductStatus.AVAILABLE:
                product.status = ProductStatus.SOLD
                product.sold_at = payment.created_at
                db.commit()

        print(f"Payment {payment.id} marked as SUCCESS")

    elif event == "payment.failed":
        payment.status = PaymentStatus.FAILED
        db.commit()
        print(f"Payment {payment.id} marked as FAILED")

    return {"message": "Webhook processed"}


@router.get("/fluxpay")
async def test_webhook(db: Session = Depends(get_db)):
    """Test endpoint to verify webhook is working"""
    return {"message": "FluxPay webhook endpoint is active"}
