import httpx
from app.core.config import get_settings

settings = get_settings()


class FluxPayError(Exception):
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(message)


class FluxPayClient:
    def __init__(self):
        self.api_url = settings.FLUXPAY_API_URL
        self.api_key = settings.FLUXPAY_API_KEY
        self.api_secret = settings.FLUXPAY_API_SECRET
        self.webhook_secret = settings.FLUXPAY_WEBHOOK_SECRET

    async def initiate_payment(
        self,
        amount: int,
        phone_number: str,
        reference: str = None,
    ) -> dict:
        """Initiate M-Pesa STK Push payment"""
        if not self.api_key or not self.api_secret:
            raise FluxPayError("FluxPay API not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.api_url}/api/v1/payments",
                    json={
                        "amount": amount,
                        "phoneNumber": phone_number,
                        "reference": reference,
                    },
                    headers={
                        "X-API-Key": self.api_key,
                        "X-API-Secret": self.api_secret,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "checkout_request_id": data.get("data", {}).get(
                            "checkoutRequestId"
                        ),
                        "amount": amount,
                        "reference": reference,
                    }
                else:
                    error = response.json()
                    raise FluxPayError(
                        error.get("message", "Payment initiation failed"),
                        code=str(response.status_code),
                    )

            except httpx.TimeoutException:
                raise FluxPayError("Payment request timed out", code="timeout")
            except httpx.RequestError as e:
                raise FluxPayError(f"Payment request failed: {str(e)}", code="request")

    async def check_payment_status(self, checkout_request_id: str) -> dict:
        """Check payment status"""
        if not self.api_key or not self.api_secret:
            raise FluxPayError("FluxPay API not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/api/v1/payments/{checkout_request_id}",
                    headers={
                        "X-API-Key": self.api_key,
                        "X-API-Secret": self.api_secret,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", {})
                else:
                    return {
                        "status": "unknown",
                        "checkoutRequestId": checkout_request_id,
                    }

            except httpx.RequestError:
                return {
                    "status": "unknown",
                    "checkoutRequestId": checkout_request_id,
                }

    async def get_business_info(self) -> dict:
        """Get business info from FluxPay"""
        if not self.api_key or not self.api_secret:
            raise FluxPayError("FluxPay API not configured")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.api_url}/api/v1/business",
                    headers={
                        "X-API-Key": self.api_key,
                        "X-API-Secret": self.api_secret,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    return response.json().get("data", {})
                else:
                    return {}

            except httpx.RequestError:
                return {}


# Singleton instance
fluxpay_client = FluxPayClient()
