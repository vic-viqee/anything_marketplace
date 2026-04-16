# FluxPay Integration Plan for Anything Marketplace

## Scenario
Anything Marketplace has signed up for FluxPay and is integrating it as their payment gateway.

---

## Integration Flow

### Step 1: Marketplace Onboards with FluxPay
1. Sign up at fluxpay.com
2. Select Growth plan (KES 4,999/mo) or Enterprise (KES 14,999/mo)
3. Complete business verification
4. Get API Keys from dashboard
5. Register webhook URL: `https://anything-marketplace.com/api/webhooks/fluxpay`

### Step 2: Technical Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        MARKETPLACE CHECKOUT                           │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Buyer clicks "Buy Now"                                          │
│ 2. Selects "Pay with M-Pesa" option                             │
│ 3. Enters phone number                                         │
│ 4. Clicks "Pay KES X"                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      MARKETPLACE BACKEND                         │
├─────────────────────────────────────────────────────────────────────────┤
│ - Call FluxPay /api/v1/payments endpoint                       │
│ - Store pending transaction                                    │
│ - Return CheckoutRequestID to frontend                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       FLUXPAY API                            │
├─────────────────────────────────────────────────────────────────────────┤
│ POST /api/v1/payments                                        │
│ {                                                            │
│   amount: 500,                                               │
│   phoneNumber: "254712345678",                               │
│   reference: "order-123"                                    │
│ }                                                            │
└────────────────────────────────────────────────────────────���────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        M-PESA                                │
├─────────────────────────────────────────────────────────────────────────┤
│ - STK Push sent to customer phone                              │
│ - Customer enters PIN                                        │
│ - Payment processed                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FLUXPAY                               │
├─────────────────────────────────────────────────────────────────────────┤
│ - Receive M-Pesa callback                                     │
│ - Update transaction status                                 │
│ - Forward webhook to Marketplace                            │
│ {                                                           │
│   event: "payment.success",                                  │
│   data: { checkoutRequestId, amount, mpesaReceiptNo }      │
│ }                                                            │
└─────────────────────────────────────────────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MARKETPLACE BACKEND                         │
├─────────────────────────────────────────────────────────────────────────┤
│ - Receive webhook                                           │
│ - Mark order as PAID                                         │
│ - Mark product as SOLD                                       │
│ - Send confirmation to buyer/seller                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Files to Modify

### Backend (FastAPI)

| File | Description |
|------|-------------|
| `app/api/v1/payments.py` | NEW - Payment endpoints |
| `app/api/v1/webhooks.py` | NEW - Webhook handler |
| `app/services/payment_service.py` | NEW - FluxPay API client |
| `app/models/models.py` | Add Transaction, Payment models |
| `app/schemas/schemas.py` | Add Payment schemas |

### Frontend (Next.js)

| File | Description |
|------|-------------|
| `frontend/src/app/checkout/page.tsx` | NEW - Checkout page |
| `frontend/src/app/product/[id]/page.tsx` | Add "Pay with M-Pesa" button |
| `frontend/src/lib/api.ts` | Add FluxPay API client |

---

## API Reference

### FluxPay Third-Party API

```bash
# Initialize payment
POST /api/v1/payments
Headers:
  X-API-Key: fpk_xxxxxxxxxxxx
  X-API-Secret: yyyyyyyyyyyy
Body:
{
  "amount": 500,
  "phoneNumber": "254712345678",
  "reference": "order-123"
}

Response:
{
  "success": true,
  "data": {
    "checkoutRequestId": "xxx",
    "amount": 500,
    "status": "PENDING"
  }
}

# Get transaction status
GET /api/v1/payments/:checkoutRequestId

# Register webhook
POST /api/v1/webhooks
{
  "url": "https://anything-marketplace.com/api/webhooks/fluxpay",
  "events": ["payment.success", "payment.failed"]
}
```

---

## Implementation Priority

### Phase 1: Basic Payment Integration (Priority)
1. Add Payment model to database
2. Create payment service (FluxPay client)
3. Add payment endpoint in backend
4. Create checkout page in frontend
5. Add webhook handler

### Phase 2: Seller Flow (Next)
1. Add seller subscription plans (Free, Basic, Standard, Premium)
2. Add plan selection on seller signup
3. Add M-Pesa for subscription payments
4. Add commission structure

### Phase 3: Advanced (Later)
1. Seller payouts (B2C disbursements)
2. Withdrawal requests
3. Commission calculations

---

## Environment Variables

```env
# FluxPay Configuration
FLUXPAY_API_URL=https://fluxpay-api.onrender.com
FLUXPAY_API_KEY=fpk_xxx
FLUXPAY_API_SECRET=xxx
FLUXPAY_WEBHOOK_SECRET=xxx
```

---

## Payment Status Flow

```
PENDING → SUCCESS
         ↓
        FAILED
```

---

## Seller Subscription Plans (Future)

| Plan | Features | Price |
|------|---------|-------|
| Free | 3 products | KES 0 |
| Basic | 20 products | KES 499/mo |
| Standard | Unlimited + verified | KES 999/mo |
| Premium | Featured + analytics | KES 1,999/mo |