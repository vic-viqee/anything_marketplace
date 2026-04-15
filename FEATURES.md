# Anything Marketplace - Features Roadmap

This document contains the complete features overview for the Anything Marketplace.

---

## Deployment

### Live URLs
- **Backend API**: https://anything-marketplace-api.onrender.com
- **Frontend**: https://anything-marketplace-web.onrender.com
- **Health Check**: https://anything-marketplace-api.onrender.com/health

### Infrastructure
- **Database**: Neon PostgreSQL (free tier)
- **Image Storage**: Cloudinary (free tier)
- **Hosting**: Render (free tier)

### Deployment Notes
- Free tier spins down after 15 min inactivity
- PostgreSQL expires in 90 days (recreate or upgrade to paid)
- For production: add Redis cache ($7+/month), upgrade DB

---

## What's Built (MVP v3)

### Core Features
- Product feed with category filters (paginated, featured listings pinned to top)
- Product search (title/description)
- Post ads with images (auto-compressed to 1200px, stored on **Cloudinary CDN**)
- Product approval system (admin moderates before live)
- **Subscription Tiers** (Free, Basic, Standard, Premium) with featured listing quotas
- **KYC Verification** (ID + selfie upload) for sellers
- **Verified Badges** for Standard/Premium tier sellers
- P2P chat messaging (WebSocket-enabled, real-time)
- In-app notifications for product approval/rejection **and new messages**
- Mark items as sold
- User ratings (1-5 stars)
- User profiles with photo, username, password management
- Dark/light mode theming
- **Report System** for flagging suspicious products/users

### Security Features
- JWT token invalidation on password change (via password_version)
- Current password verification required to change password
- File size validation (10MB max)
- CORS configuration
- Input validation (Pydantic)
- Storage abstraction (local/S3/Cloudinary via STORAGE_TYPE env var)

### Admin Features
- Analytics dashboard (pie + bar charts)
- Product moderation (approve/reject/bulk)
- User management (roles, deactivate, suspend, delete, **search**)
- **KYC Review** - Approve/reject seller identity verification
- **Subscription Management** - View and update seller tiers
- **Reports Management** - Review and resolve flagged content
- Support ticket system
- Activity logs
- Category management (create new categories)
- CSV export
- Broadcast to all users
- Direct notification to users

---

## User Roles

| Role | Abilities |
|------|----------|
| **Customer** | Browse products, message sellers, rate after purchase, report suspicious content |
| **Seller** | All customer abilities + post listings + subscribe to tiers + submit KYC |
| **Admin** | All abilities + approve products, manage users, review KYC, manage subscriptions, handle reports |

---

## How It Works

### For Buyers (Customers)
1. **Browse** - Visit the home page to see approved products
2. **Search** - Filter by category or browse all listings
3. **View Details** - Click any product to see full details, price, and seller info
4. **Contact Seller** - Use inbuilt chat OR WhatsApp to message the seller
5. **Pay on Delivery** - Meet the seller, inspect the item, and pay when you receive it

### For Sellers
1. **Register** - Create account, choose "Seller" role, select subscription tier
2. **Submit KYC** - Upload ID card front and selfie for identity verification
3. **Post Ad** - Fill in title, description, price, and upload an image
4. **Wait for Approval** - Your product won't appear until admin approves it
5. **Check Status** - Visit "My Products" to see pending/approved status
6. **Feature Listings** - Use your tier's featured quota to pin listings to top
7. **Get Notified** - Receive in-app notification when your product is approved
8. **Close Sale** - When buyer pays, mark the item as "Sold"

### For Admins
1. **Review Products** - Go to admin dashboard to see pending products
2. **Approve or Reject** - Click to approve (goes live) or reject (notified to seller)
3. **Manage Users** - View all users, change roles, suspend, or delete
4. **Review KYC** - Approve or reject seller identity verification
5. **Manage Subscriptions** - View and update seller subscription tiers
6. **Handle Reports** - Review and resolve reports about suspicious content
7. **View Analytics** - See total users, products, pending approvals, and sold items

---

## Admin Dashboard Features

### Priority 1: Core Essentials (Built)

| Feature | Status |
|---------|--------|
| **User Management** - View all users, change roles, deactivate accounts
| **Product Oversight** - Approve/reject listings, delete any product
| **Analytics** - Better dashboard with GMV, category breakdown

### Priority 2: Trust & Safety

| Feature | Status |
|---------|--------|
| **Ticket System** - Users can report issues | ✅ Built |
| **Dispute Resolution** - View buyer-seller chats for mediation | ✅ Built |
| **Review Moderation** - Delete inappropriate ratings | ✅ Built |

### Priority 3: Revenue & Payments (Later)

| Feature | Status |
|---------|--------|
| Commission Settings - Set transaction fees |
| Payouts - Manage seller payouts |
| Refund Handling - Process refunds |

### Priority 4: Advanced

| Feature | Status |
|---------|--------|
| **Subscription Model** - Membership/tier access | ✅ Done |
| **Business Verification** - ID/credential checking (KYC) | ✅ Done |
| **Full Ban System** - Ban with reason + duration | ✅ Done |
| **Report/Flag content** - Users can report suspicious products/users | ✅ Done |
| Email Automation - Auto-emails for events |
| User Behavior Analytics - Detailed tracking |

---

---

## Known Issues

- **Rate limiting**: Disabled due to slowapi incompatibility with Python 3.14 (Render default)
- **Redis cache**: Disabled in production (free tier doesn't include Redis)

---

## Recent Updates

### Subscription Tiers & KYC (2026-04-15)
- Added subscription tiers: Free (0 featured), Basic (1), Standard (3), Premium (5)
- Implemented KYC verification with ID + selfie upload
- Verified badge for Standard/Premium tier sellers
- Featured listings pinned to top of feed (7-day duration)
- Admin dashboard with KYC review, subscription management, reports tabs
- Report system for flagging suspicious products/users
- Suspended users hidden from product feed

### Bug Fixes (2026-04-11)
- Fixed images not displaying on Cloudinary (now handles full CDN URLs)
- Fixed missing notifications for new messages (now creates DB notification)

---

## Planned Features

### Admin Enhancements (Medium)
- Product search in Products tab
- Activity logs UI tab (✅ Done)
- Category management UI tab (✅ Done)
- Bulk actions for products (approve/reject multiple)

### Core Improvements (Medium)
- Product view tracking - Allow sellers to see view counts
- Pagination UI for feed (page numbers vs infinite scroll)
- Better empty states and loading skeletons

### Security (High)
- Rate limiting (currently disabled - slowapi Python 3.14 issue)
- ✅ Token invalidation on password change (password_version column)
- Phone verification (SMS OTP)
- Password reset flow

### Integration (High)
- WhatsApp Business integration (currently just a link)
- Push notifications
- Shipping integration
- Online payment support (M-Pesa STK push - planned)

---

## Authentication Options (Planned)

### Phase 2: Phone Verification (SMS OTP)
- Send 4-6 digit code via SMS on registration
- User enters code to complete signup
- **Provider**: Africa's Talking (recommended for Kenya pricing)
- **Cost**: ~KSh 1-5 per SMS
- Prevents fake accounts with random numbers

### Phase 2: WhatsApp Authentication
- One-time code via WhatsApp instead of SMS
- **Pros**: Cheaper than SMS, reliable in Kenya, most users have WhatsApp
- Can be offered as alternative to SMS OTP

### Phase 3: Social Login
| Provider | Status | Notes |
|----------|--------|-------|
| Google | Planned | Easy integration with NextAuth.js |
| Apple | Planned | Good for iOS users |
| Facebook | Later | Declining usage, privacy concerns |

### Phase 4: Identity Verification
| Method | Status | Notes |
|--------|--------|-------|
| eCitizen Integration | Planned | Official Kenyan ID verification |
| National ID OCR | Planned | Scan Kenyan ID card |
| M-Pesa Verification | Planned | Verify via existing M-Pesa number |

### Passwordless Options (Future)
| Method | Status | Notes |
|--------|--------|-------|
| Magic Links | Future | Email link to login |
| Biometric Auth | Future | Fingerprint/Face ID |

### Why Phone Verification Matters
1. **Trust**: Confirms user has access to the number
2. **Contact**: Can reach users for transactions
3. **Fraud Prevention**: Makes fake accounts harder
4. **M-Pesa Ready**: Phone number needed for payments

### User Features (Medium)
- Multiple images per product
- Favorites/Wishlist
- Email notifications
- ✅ Report/Flag content

### Lower Priority
- Email Automation - Auto-emails for events
- Store reviews/ratings

---

## Technical Notes

- Products require admin approval before appearing in public feed
- Featured listings appear at top of feed (sorted first, 7-day duration)
- Sellers can view their products status in "My Products" page
- In-app notifications are sent when products are approved/rejected **and for new messages**
- Images are auto-compressed to 1200px max, stored on **Cloudinary CDN**
- Admin dashboard has 11 tabs: Analytics, Products, Users, KYC, Subscriptions, Reports, Tickets, Reviews, Broadcast, Activity, Categories

---

## Technical Infrastructure

| Component | Local | Production |
|-----------|-------|-----------|
| Database | PostgreSQL (Docker) | Neon PostgreSQL |
| Cache | Redis (Docker) | Disabled (free tier) |
| Storage | Local /uploads | Cloudinary CDN |
| Hosting | Localhost | Render |

---

_Last updated: 2026-04-15 (includes subscription tiers, KYC verification, reports, suspended users)_