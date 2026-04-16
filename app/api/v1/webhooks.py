from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.models import Payment, PaymentStatus, Product, ProductStatus, User
from app.services.payment_service import fluxpay_client
import hmac
import hashlib

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class FluxPayWebhookPayload(BaseModel):
    event: str
    timestamp: str
    data: dict


def verify_webhook_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature from FluxPay"""
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

    body = await request.json()

    # Log the webhook for debugging
    print(f"FluxPay webhook received: {body}")

    event = body.get("event")
    data = body.get("data", {})

    checkout_request_id = data.get("checkoutRequestId") or data.get(
        "checkout_request_id"
    )
    payment_status = data.get("status", "").upper()

    if not checkout_request_id:
        return {"message": "No checkout request ID"}

    # Find payment by checkout request ID
    payment = (
        db.query(Payment)
        .filter(Payment.fluxpay_checkout_request_id == checkout_request_id)
        .first()
    )

    if not payment:
        print(f"Payment not found for checkout_request_id: {checkout_request_id}")
        return {"message": "Payment not found"}

    if event == "payment.success":
        payment.status = PaymentStatus.SUCCESS
        payment.mpesa_receipt_no = data.get("mpesaReceiptNo")
        db.commit()

        # Mark product as sold
        if payment.product_id:
            product = db.query(Product).filter(Product.id == payment.product_id).first()
            if product:
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
