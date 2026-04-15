# Anything Marketplace

A P2P (peer-to-peer) marketplace MVP for buying and selling anything. Built with a "Pay on Delivery" model - no payment processing, just connect buyers and sellers directly. Designed for Kenyan users with M-Pesa integration support.

## What It Does

- **Browse Listings**: View products in a paginated feed with category filters, featured listings pinned to top
- **Post Ads**: Sellers can list items with images (auto-compressed)
- **Product Approval**: Admin must approve seller products before they appear in feed
- **Subscription Tiers**: Free, Basic, Standard, and Premium plans with different featured listing limits
- **KYC Verification**: Sellers required to submit ID and selfie for verification (Standard/Premium get verified badges)
- **Chat**: Built-in P2P messaging between buyers and sellers
- **Mark as Sold**: Sellers mark items as sold after transaction
- **Rate**: Buyers can rate sellers (1-5 stars) after completed sales
- **Report System**: Users can report suspicious products or users
- **User Profiles**: Update username, profile photo, and password
- **Dark/Light Mode**: Toggle between themes

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database (Neon on production)
- **Redis** - Caching for feed endpoints (optional)
- **SQLAlchemy** - ORM for database operations
- **JWT** - Token-based authentication
- **Pillow** - Image compression
- **Cloudinary** - Image storage (production)

### Frontend
- **Next.js 16** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Utility-first styling with OKLCH theme
- **Zustand** - Lightweight state management (auth store)
- **Axios** - HTTP client

## Project Structure

```
marketplace/
├── app/                    # FastAPI backend
│   ├── api/v1/            # API endpoints
│   ├── core/              # Config, DB, security
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── services/          # Business logic
│   └── main.py            # App entry point
├── frontend/              # Next.js frontend
│   └── src/
│       ├── app/           # Pages
│       ├── components/    # React components
│       ├── context/       # State stores
│       ├── lib/           # API client
│       └── types/         # TypeScript types
├── uploads/               # Local image storage
├── docker-compose.yml     # Docker orchestration
└── tests/                 # Backend tests
```

## User Roles

- **Customer**: Browse products, message sellers, rate after purchase, report suspicious content
- **Seller**: All customer abilities + post new listings + subscribe to plans + submit KYC
- **Admin**: All abilities + approve/reject products, manage users, review KYC, manage subscriptions, handle reports

## Running Locally

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Option 1: Docker Only (Backend)

```bash
# Start PostgreSQL, Redis, and FastAPI
docker-compose up --build

# API runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Option 2: Full Stack Development

```bash
# 1. Start infrastructure
docker-compose up -d postgres redis

# 2. Setup Python backend
cd marketplace
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. Setup Next.js frontend
cd frontend
npm install
npm run dev

# Frontend runs at http://localhost:3000
```

### Environment Variables (Local Development)

Create `.env` file in project root:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=supersecretkey123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Rate limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTH=10/minute

# Storage
STORAGE_TYPE=local
```

For frontend, create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Environment Variables (Production - Render)

For backend on Render:
```
DATABASE_URL=postgresql://neondb_owner:password@ep-xxx.eu-west-2.aws.neon.tech/neondb?sslmode=require
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
SECRET_KEY=random_32_char_string
DEBUG=false
CORS_ORIGINS=["https://your-frontend.onrender.com"]
REDIS_HOST=
```

For frontend on Render:
```
NEXT_PUBLIC_API_URL=https://your-backend.onrender.com
```

## API Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user with role and subscription tier
- `POST /api/v1/auth/login` - Login (phone OR username)
- `GET /api/v1/auth/me` - Get current user
- `PATCH /api/v1/auth/me` - Update username or password
- `POST /api/v1/auth/me/profile-image` - Upload profile photo
- `POST /api/v1/auth/me/kyc` - Submit KYC verification (ID + selfie)

### Products
- `GET /api/v1/products/feed` - Latest approved listings (paginated, cached, featured first)
- `GET /api/v1/products` - All listings (with search)
- `GET /api/v1/products/{id}` - Single product
- `POST /api/v1/products` - Create listing (seller required)
- `PUT /api/v1/products/{id}` - Update listing
- `DELETE /api/v1/products/{id}` - Delete listing
- `POST /api/v1/products/{id}/mark-sold` - Mark as sold
- `POST /api/v1/products/{id}/feature` - Feature a listing (uses tier quota)
- `DELETE /api/v1/products/{id}/feature` - Remove featured status
- `GET /api/v1/products/categories` - List categories
- `POST /api/v1/products/categories` - Create category
- `POST /api/v1/products/{id}/ratings` - Rate seller
- `GET /api/v1/products/users/{id}/ratings` - Get user rating stats
- `GET /api/v1/products/my-products` - Seller's products

### Reports
- `POST /api/v1/reports` - Report a product or user

### Admin
- `GET /api/v1/admin/analytics` - Dashboard stats
- `GET /api/v1/admin/products/pending` - Pending products
- `POST /api/v1/admin/products/{id}/approve` - Approve product
- `POST /api/v1/admin/products/{id}/reject` - Reject product
- `POST /api/v1/admin/products/bulk` - Bulk approve/reject
- `GET /api/v1/admin/users` - List users (searchable)
- `GET /api/v1/admin/users/{id}` - Get user details
- `PATCH /api/v1/admin/users/{id}/role` - Update user role
- `PATCH /api/v1/admin/users/{id}/deactivate` - Toggle user status
- `PATCH /api/v1/admin/users/{id}/suspend` - Suspend/unsuspend user
- `PATCH /api/v1/admin/users/{id}/subscription` - Update subscription tier
- `DELETE /api/v1/admin/users/{id}` - Delete user
- `DELETE /api/v1/admin/products/{id}` - Delete product
- `GET /api/v1/admin/kyc/pending` - Get pending KYC submissions
- `POST /api/v1/admin/kyc/{id}/approve` - Approve KYC
- `POST /api/v1/admin/kyc/{id}/reject` - Reject KYC
- `GET /api/v1/admin/reports` - List reports
- `PATCH /api/v1/admin/reports/{id}` - Update report status
- `GET /api/v1/admin/export/users.csv` - Export users CSV
- `GET /api/v1/admin/export/products.csv` - Export products CSV
- `POST /api/v1/admin/notify` - Send notification to user

### Chat
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations` - List user's conversations
- `GET /api/v1/chat/conversations/{id}` - Get messages
- `POST /api/v1/chat/messages` - Send message
- `POST /api/v1/chat/conversations/{id}/read` - Mark read
- `GET /api/v1/chat/nudges` - Get conversation nudges
- `GET /api/v1/chat/unread-count` - Get unread message count

### WebSocket
- `WS /api/v1/ws/chat?token={jwt}` - Real-time chat connection

### Admin
- `GET /api/v1/admin/analytics` - Dashboard stats
- `GET /api/v1/admin/products/pending` - Pending products
- `POST /api/v1/admin/products/{id}/approve` - Approve product
- `POST /api/v1/admin/products/{id}/reject` - Reject product
- `POST /api/v1/admin/products/bulk` - Bulk approve/reject
- `GET /api/v1/admin/users` - List users (searchable)
- `GET /api/v1/admin/users/{id}` - Get user details
- `PATCH /api/v1/admin/users/{id}/role` - Update user role
- `PATCH /api/v1/admin/users/{id}/deactivate` - Toggle user status
- `DELETE /api/v1/admin/users/{id}` - Delete user
- `DELETE /api/v1/admin/products/{id}` - Delete product
- `GET /api/v1/admin/export/users.csv` - Export users CSV
- `GET /api/v1/admin/export/products.csv` - Export products CSV
- `POST /api/v1/admin/notify` - Send notification to user

## Frontend Pages

| Route | Description |
|-------|-------------|
| `/` | Product feed with category filters |
| `/login` | Login (phone or username) |
| `/register` | Registration with role selection |
| `/post` | Post new listing (sellers only) |
| `/profile` | Settings: Profile & Account tabs |
| `/messages` | Chat conversations |
| `/admin` | Admin dashboard (admins only) |

## Features

### Subscription Tiers

| Tier | Featured Listings | Verified Badge | Price |
|------|-------------------|----------------|-------|
| Free | 0 | No | Free |
| Basic | 1 | No | Contact admin |
| Standard | 3 | Yes | Contact admin |
| Premium | 5 | Yes | Contact admin |

- Featured listings appear at the top of the product feed
- Featured status lasts for 7 days by default
- Standard and Premium tiers include verified seller badge
- Existing sellers are grandfathered (no KYC required for them)

### Image Handling
- Images are automatically compressed on upload (max 1200px width for products, 400px for profiles)
- Converted to JPEG for consistent format and smaller file sizes
- Local development: stored in `/uploads` directory
- Production: uploaded to Cloudinary CDN (set STORAGE_TYPE=cloudinary)

### Authentication
- JWT-based authentication with 60-minute token expiry
- Login accepts either phone number or username
- Secure password hashing with bcrypt
- Token invalidation on password change (password_version increments, invalidates old tokens)

### Caching
- Product feed is cached in Redis (5-minute TTL)
- Reduces database load for frequently accessed endpoints

### Security
- Token invalidation on password change
- File size validation (10MB max)
- CORS restricted to configured origins
- Current password required to change password

### Theming
- Light/dark mode toggle in navbar
- Persists preference to localStorage
- Respects system preference on first visit

## Testing

```bash
# Run all backend tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with coverage
python -m pytest --cov=app --cov-report=term-missing
```

## Admin Features

1. **Analytics Dashboard**: View total users, products, pending approvals, and sold items
2. **Product Moderation**: Approve or reject seller listings before they appear publicly
3. **User Management**: Change roles (customer/seller/admin), suspend users, or delete accounts
4. **KYC Review**: Review and approve/reject seller identity verification submissions
5. **Subscription Management**: View and update seller subscription tiers
6. **Reports Management**: Review and resolve user reports about suspicious products or users

---

## How It Works

Anything Marketplace uses a **"Pay on Delivery"** model - buyers and sellers connect directly, and payment happens when the buyer receives the item.

### For Buyers

1. **Browse** - Visit the home page to see approved products
2. **Search** - Filter by category or browse all listings  
3. **View Details** - Click any product to see full details, price, and seller info
4. **Contact Seller** - Use inbuilt chat OR WhatsApp to message the seller
5. **Pay on Delivery** - Meet the seller, inspect the item, and pay when you receive it

### For Sellers

1. **Register** - Create account, choose "Seller" role, select subscription tier
2. **Submit KYC** - Upload ID card front and selfie for identity verification
3. **Post Ad** - Fill in title, description, price, and upload an image
4. **Wait for Approval** - Your product won't appear in the feed until an admin approves it
5. **Check Status** - Visit "My Products" to see pending/approved status
6. **Feature Listings** - Use your tier's featured quota to pin listings to top
7. **Get Notified** - Receive in-app notification when your product is approved
8. **Close Sale** - When buyer pays, mark the item as "Sold"

### For Admins

1. **Review Products** - Go to `/admin` dashboard to see pending products
2. **Approve or Reject** - Click to approve (goes live) or reject (seller is notified)
3. **Manage Users** - View all users, change roles, suspend accounts, or delete
4. **Review KYC** - Approve or reject seller identity verification submissions
5. **Manage Subscriptions** - View and update seller subscription tiers
6. **Handle Reports** - Review and resolve reports about suspicious products/users
7. **View Analytics** - See total users, products, pending approvals, and sold items

### Key Workflows

**Product Approval Flow:**
```
Seller posts product → Product status: "Pending Approval" → Admin approves → Product goes live → Seller notified
```

**Buyer-Seller Communication:**
```
Buyer views product → Clicks "Message Seller" OR "WhatsApp" → Inbuilt chat OR WhatsApp opens → Agree on meeting → Pay on delivery
```

**Selling an Item:**
```
Seller receives buyer → Shows item → Buyer pays → Seller marks item as "Sold" → Item removed from feed
```