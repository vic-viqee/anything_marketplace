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

## What's Built (MVP v2)

### Core Features
- Product feed with category filters (paginated, conditionally cached in Redis)
- Product search (title/description)
- Post ads with images (auto-compressed to 1200px, stored on **Cloudinary CDN**)
- Product approval system (admin moderates before live)
- P2P chat messaging (WebSocket-enabled, real-time)
- In-app notifications for product approval/rejection **and new messages**
- Mark items as sold
- User ratings (1-5 stars)
- User profiles with photo, username, password management
- Dark/light mode theming

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
- User management (roles, deactivate, delete, **search**)
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
| **Customer** | Browse products, message sellers, rate after purchase |
| **Seller** | All customer abilities + post new listings |
| **Admin** | All abilities + approve/reject products, manage users, view analytics |

---

## How It Works

### For Buyers (Customers)
1. **Browse** - Visit the home page to see approved products
2. **Search** - Filter by category or browse all listings
3. **View Details** - Click any product to see full details, price, and seller info
4. **Contact Seller** - Use inbuilt chat OR WhatsApp to message the seller
5. **Pay on Delivery** - Meet the seller, inspect the item, and pay when you receive it

### For Sellers
1. **Register** - Create account and choose "Seller" role
2. **Post Ad** - Fill in title, description, price, and upload an image
3. **Wait for Approval** - Your product won't appear until admin approves it
4. **Check Status** - Visit "My Products" to see pending/approved status
5. **Get Notified** - Receive in-app notification when your product is approved
6. **Close Sale** - When buyer pays, mark the item as "Sold"

### For Admins
1. **Review** - Go to admin dashboard to see pending products
2. **Approve or Reject** - Click to approve (goes live) or reject (notified to seller)
3. **Manage Users** - View all users, change roles, or delete accounts
4. **View Analytics** - See total users, products, pending approvals, and sold items

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

### Priority 4: Advanced (Later)

| Feature | Status |
|---------|--------|
| Subscription Model - Membership/tier access |
| Email Automation - Auto-emails for events |
| User Behavior Analytics - Detailed tracking |
| Business Verification - ID/credential checking |
| **Full Ban System** - Ban with reason + duration (simpler deactivate available now) |

---

---

## Known Issues

- **Rate limiting**: Disabled due to slowapi incompatibility with Python 3.14 (Render default)
- **Redis cache**: Disabled in production (free tier doesn't include Redis)

---

## Recent Updates

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
- Token invalidation on password change (password_version column)
- Email verification
- Password reset flow

### Integration (High)
- WhatsApp Business integration (currently just a link)
- Push notifications
- Shipping integration
- Online payment support

### User Features (Medium)
- Multiple images per product
- Favorites/Wishlist
- Email notifications
- Report/Flag content

### Lower Priority
- Subscription Model - Membership/tier access
- Email Automation - Auto-emails for events
- Store reviews/ratings

---

## Technical Notes

- Products require admin approval before appearing in public feed
- Sellers can view their products status in "My Products" page
- In-app notifications are sent when products are approved/rejected **and for new messages**
- Images are auto-compressed to 1200px max, stored on **Cloudinary CDN**
- Admin dashboard has 8 tabs: Analytics, Products, Users, Tickets, Reviews, Broadcast, Activity, Categories

---

## Technical Infrastructure

| Component | Local | Production |
|-----------|-------|-----------|
| Database | PostgreSQL (Docker) | Neon PostgreSQL |
| Cache | Redis (Docker) | Disabled (free tier) |
| Storage | Local /uploads | Cloudinary CDN |
| Hosting | Localhost | Render |

---

_Last updated: 2026-04-11 (includes all admin tabs, Cloudinary images, message notifications)_