# Anything Marketplace

A P2P (peer-to-peer) marketplace MVP for buying and selling anything. Built with a "Pay on Delivery" model - no payment processing, just connect buyers and sellers directly.

## What It Does

- **Browse Listings**: View products in a paginated feed with category filters
- **Post Ads**: Sellers can list items with images (auto-compressed)
- **Product Approval**: Admin must approve seller products before they appear in feed
- **Chat**: Built-in P2P messaging between buyers and sellers
- **Mark as Sold**: Sellers mark items as sold after transaction
- **Rate**: Buyers can rate sellers (1-5 stars) after completed sales
- **User Profiles**: Update username, profile photo, and password
- **Dark/Light Mode**: Toggle between themes

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching for feed endpoints
- **SQLAlchemy** - ORM for database operations
- **JWT** - Token-based authentication
- **Pillow** - Image compression

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

- **Customer**: Browse products, message sellers, rate after purchase
- **Seller**: All customer abilities + post new listings
- **Admin**: All abilities + approve/reject products, manage users, view analytics

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

### Environment Variables

Create `.env` file in project root:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=supersecretkey123456789
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads

# Default admin account (for development)
ADMIN_PHONE=+254700000010
ADMIN_PASSWORD=password
```

For frontend, create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Default Accounts

| Phone | Password | Role |
|-------|----------|------|
| +254700000010 | password | Admin |
| +254700000011 | password | Seller |
| +254700000002 | test123 | Customer |

You can also login with username instead of phone number.

## API Endpoints

### Auth
- `POST /api/v1/auth/register` - Register new user (returns token + user)
- `POST /api/v1/auth/login` - Login (phone OR username)
- `GET /api/v1/auth/me` - Get current user
- `PATCH /api/v1/auth/me` - Update username or password
- `POST /api/v1/auth/me/profile-image` - Upload profile photo

### Products
- `GET /api/v1/products/feed` - Latest approved listings (paginated, cached)
- `GET /api/v1/products` - All listings
- `GET /api/v1/products/{id}` - Single product
- `POST /api/v1/products` - Create listing (seller required)
- `PUT /api/v1/products/{id}` - Update listing
- `DELETE /api/v1/products/{id}` - Delete listing
- `POST /api/v1/products/{id}/mark-sold` - Mark as sold
- `GET /api/v1/products/categories` - List categories
- `POST /api/v1/products/{id}/ratings` - Rate seller
- `GET /api/v1/products/users/{id}/ratings` - Get user rating stats

### Chat
- `POST /api/v1/chat/conversations` - Create conversation
- `GET /api/v1/chat/conversations` - List user's conversations
- `GET /api/v1/chat/conversations/{id}` - Get messages
- `POST /api/v1/chat/messages` - Send message
- `POST /api/v1/chat/conversations/{id}/read` - Mark read
- `GET /api/v1/chat/nudges` - Get conversation nudges
- `GET /api/v1/chat/unread-count` - Get unread message count

### Admin
- `GET /api/v1/admin/analytics` - Dashboard stats
- `GET /api/v1/admin/products/pending` - Pending products
- `POST /api/v1/admin/products/{id}/approve` - Approve product
- `POST /api/v1/admin/products/{id}/reject` - Reject product
- `GET /api/v1/admin/users` - List users
- `PATCH /api/v1/admin/users/{id}/role` - Update user role
- `DELETE /api/v1/admin/users/{id}` - Delete user
- `DELETE /api/v1/admin/products/{id}` - Delete product

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

### Image Handling
- Images are automatically compressed on upload (max 1200px width for products, 400px for profiles)
- Converted to JPEG for consistent format and smaller file sizes
- Stored locally in `/uploads` directory

### Authentication
- JWT-based authentication with 60-minute token expiry
- Login accepts either phone number or username
- Secure password hashing with bcrypt

### Caching
- Product feed is cached in Redis (5-minute TTL)
- Reduces database load for frequently accessed endpoints

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
3. **User Management**: Change roles (customer/seller/admin) or delete users

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

1. **Register** - Create account and choose "Seller" role
2. **Post Ad** - Fill in title, description, price, and upload an image
3. **Wait for Approval** - Your product won't appear in the feed until an admin approves it
4. **Check Status** - Visit "My Products" to see pending/approved status
5. **Get Notified** - Receive in-app notification when your product is approved
6. **Close Sale** - When buyer pays, mark the item as "Sold"

### For Admins

1. **Review** - Go to `/admin` dashboard to see pending products
2. **Approve or Reject** - Click to approve (goes live) or reject (seller is notified)
3. **Manage Users** - View all users, change roles, or delete accounts
4. **View Analytics** - See total users, products, pending approvals, and sold items

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