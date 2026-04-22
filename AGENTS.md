# AGENTS.md - Anything Marketplace Developer Profile

## Role: Full Stack Developer (FastAPI + Next.js)
- **Primary Objective:** Build and maintain a P2P Marketplace MVP.
- **Workflow:** 1. Read `PLANS.md` (if exists).
  2. Identify the next uncompleted task.
  3. Propose a technical implementation plan.
  4. Wait for user approval.
  5. Execute code, verify, and update status.

---

## Project Overview

**Anything Marketplace** - A P2P (peer-to-peer) marketplace for buying and selling anything with "Pay on Delivery" model.

### Features
- Product feed with category filters (paginated, Redis-cached)
- Product search (title/description)
- Post ads with images (auto-compressed to 1200px max)
- Product approval system (admin moderates before live)
- **Seller verification** - Sellers require manual admin verification before posting
- WhatsApp-style chat with read receipts (single tick sent, double tick read)
- Built-in P2P chat messaging (WebSocket-enabled, real-time)
- In-app notifications (product approved/rejected)
- Mark items as sold
- User ratings (1-5 stars)
- User profiles with photo, username, password management
- Dark/light mode theming
- Product detail page with seller info
- Contact seller via inbuilt chat or WhatsApp (pre-filled messages with phone numbers)
- Admin dashboard with analytics, bulk actions, activity logs, seller verification
- Support ticket system (reports, disputes)
- CSV export for users/products
- JWT token invalidation on password change
- Rate limiting on auth endpoints
- Edge case validation (title 3-100 chars, price 0-100M, description max 2000 chars)
- Auto-migration on startup for missing database columns

### User Roles
- **Customer**: Browse, message sellers, rate after purchase
- **Seller**: Customer + post listings (requires admin verification)
- **Admin**: All abilities + approve/reject products, manage users, verify sellers, view analytics

---

## Technical Stack

### Backend
- **FastAPI** - Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching for feed endpoints
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT** - Token-based auth with password versioning
- **Pillow** - Image compression
- **Passlib** - Password hashing
- **SlowAPI** - Rate limiting

### Frontend
- **Next.js 16** - React framework (App Router)
- **TypeScript** - Type safety
- **Tailwind CSS v4** - Styling (OKLCH theme)
- **Zustand** - State management (auth store)
- **Axios** - HTTP client
- **Lucide React** - Icons

---

## Build / Run Commands

### Backend
```bash
# Create venv and install
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with Docker
docker-compose up --build

# Run tests
python -m pytest tests/ -v
python -m pytest tests/test_auth.py -v
python -m pytest --cov=app --cov-report=term-missing

# Lint
ruff check . --fix

# Type check
python -m mypy app --ignore-missing-imports
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run development
npm run dev

# Build for production
npm run build

# Run linter
npm run lint
```

---

## File Structure

### Backend (`/app`)
```
app/
├── api/
│   └── v1/
│       ├── auth.py         # Auth: register, login, profile update, image upload
│       ├── products.py     # Products, categories, ratings, my-products
│       ├── chat.py         # Messaging, conversations
│       ├── ratings.py      # Rating endpoints
│       ├── nudge.py        # Chat nudges
│       ├── admin.py        # Admin: analytics, user/product management
│       ├── notifications.py # In-app notifications
│       ├── tickets.py      # Support tickets
│       └── websocket.py     # WebSocket endpoint for real-time chat
├── core/
│   ├── config.py          # Settings (from .env)
│   ├── database.py        # SQLAlchemy setup, get_db
│   └── security.py        # JWT, password hashing, get_current_active_user
├── models/
│   └── models.py          # SQLAlchemy: User, Product, Category, Conversation, Message, Rating, Notification
├── schemas/
│   └── schemas.py         # Pydantic: UserCreate, UserLogin, ProductCreate, etc.
├── services/
│   ├── auth_service.py    # Password hashing, token creation
│   ├── redis_service.py   # Redis caching
│   ├── storage_service.py # Storage abstraction (local/S3/Cloudinary)
│   └── websocket_manager.py # WebSocket connection manager
└── main.py                # FastAPI app entry, CORS, routers
```

### Frontend (`/frontend/src`)
```
frontend/src/
├── app/
│   ├── layout.tsx         # Root layout with fonts
│   ├── page.tsx           # Product feed (/)
│   ├── globals.css        # Tailwind theme (OKLCH colors)
│   ├── login/page.tsx     # Login (phone or username)
│   ├── register/page.tsx  # Registration
│   ├── post/page.tsx      # Create listing
│   ├── my-products/page.tsx   # Seller's product listings with status
│   ├── notifications/page.tsx # In-app notifications
│   ├── profile/page.tsx   # Settings (profile + account tabs)
│   ├── messages/page.tsx  # Chat conversations
│   ├── admin/page.tsx     # Admin dashboard
│   └── product/[id]/page.tsx  # Product detail
├── components/
│   ├── Navbar.tsx         # Navigation with dark/light toggle, notifications badge
│   ├── ClientLayout.tsx   # Client wrapper with ThemeProvider
│   ├── ProductCard.tsx    # Product card (uses img, not Next Image)
│   ├── PhoneInput.tsx     # Phone number input
│   └── PasswordInput.tsx  # Password input with show/hide
├── context/
│   ├── auth-store.ts      # Zustand auth state (user, token, login/logout)
│   └── theme.tsx          # Theme context (dark/light mode)
├── lib/
│   └── api.ts             # Axios API client (authApi, productsApi, chatApi, adminApi, notificationsApi)
└── types/
    └── index.ts           # TypeScript interfaces
```

---

## Database Schema

### Users Table
- `id` (PK)
- `phone` (unique, indexed)
- `username` (unique, indexed, nullable)
- `hashed_password`
- `password_version` (integer - for token invalidation)
- `profile_image` (nullable)
- `role` (enum: customer/seller/admin)
- `is_active` (boolean)
- `is_identity_verified` (boolean - requires admin verification for sellers)
- `subscription_tier`, `subscription_expires_at`
- `kyc_status`, `kyc_id_number`, `kyc_id_front_url`, `kyc_selfie_url`
- `is_suspended`, `suspension_reason`
- `created_at`, `updated_at`

### Products Table
- `id` (PK)
- `title`, `description`, `price`
- `image_url` (nullable)
- `status` (enum: available/sold/archived)
- `is_approved` (boolean)
- `is_featured`, `featured_until`, `featured_by_admin`
- `seller_id` (FK to users)
- `category_id` (FK to categories, nullable)
- `created_at`, `updated_at`, `sold_at`

### Categories Table
- `id` (PK)
- `name`, `slug` (unique)
- `created_at`

### Conversations Table
- `id` (PK)
- `product_id`, `initiator_id`, `receiver_id`
- `last_message_at`, `created_at`

### Messages Table
- `id` (PK)
- `conversation_id`, `sender_id`
- `content`, `is_read`, `is_delivered`
- `created_at`

### Ratings Table
- `id` (PK)
- `rater_id`, `rated_user_id`, `product_id`
- `stars` (1-5), `comment` (nullable)
- `created_at`

### Notifications Table
- `id` (PK)
- `user_id` (FK to users)
- `notification_type` (enum: product_approved, product_rejected, new_message, new_rating)
- `title`, `message`
- `is_read` (boolean)
- `related_id` (nullable - links to related entity)
- `created_at`

### ActivityLog Table
- `id` (PK)
- `user_id`, `action`, `entity_type`, `entity_id`, `details`
- `created_at`

### Reports Table
- `id` (PK)
- `reporter_id`, `reported_user_id`, `reported_product_id`, `reported_conversation_id`
- `reason`, `description`, `status`
- `created_at`, `updated_at`

---

## API Endpoints

### Auth (`/api/v1/auth`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /register | Register new user | No |
| POST | /login | Login (phone or username) | No |
| GET | /me | Get current user | Yes |
| PATCH | /me | Update username/password | Yes |
| POST | /me/profile-image | Upload profile photo | Yes |

### Products (`/api/v1/products`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /feed | Paginated approved listings (cached) | No |
| GET | / | All approved listings (with search) | No |
| GET | /{id} | Single product | No |
| POST | / | Create listing | Seller+ |
| PUT | /{id} | Update listing | Owner |
| DELETE | /{id} | Delete listing | Owner |
| POST | /{id}/mark-sold | Mark as sold | Owner |
| GET | /categories | List categories | No |
| POST | /categories | Create category | Yes |
| POST | /{id}/ratings | Rate seller | Customer |
| GET | /users/{id}/ratings | Get user ratings | No |
| GET | /my-products | Seller's products | Seller+ |

### Chat (`/api/v1/chat`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /conversations | Create conversation | Yes |
| GET | /conversations | List conversations | Yes |
| GET | /conversations/{id} | Get messages | Yes |
| POST | /messages | Send message | Yes |
| POST | /conversations/{id}/read | Mark read | Yes |
| GET | /nudges | Get nudges | Yes |
| GET | /unread-count | Get unread count | Yes |

### WebSocket (`/api/v1/ws/chat`)
| Endpoint | Description |
|----------|-------------|
| /ws/chat?token={jwt} | Real-time chat (WebSocket) |

### Admin (`/api/v1/admin`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /analytics | Dashboard stats | Admin |
| GET | /products/pending | Pending products | Admin |
| POST | /products/{id}/approve | Approve product | Admin |
| POST | /products/{id}/reject | Reject product | Admin |
| POST | /products/bulk | Bulk approve/reject | Admin |
| GET | /users | List users (with search/filter) | Admin |
| PATCH | /users/{id}/role | Update role | Admin |
| PATCH | /users/{id}/deactivate | Toggle user status | Admin |
| POST | /users/{id}/verify | Verify seller | Admin |
| POST | /users/{id}/unverify | Revoke seller verification | Admin |
| DELETE | /users/{id} | Delete user | Admin |
| DELETE | /products/{id} | Delete product | Admin |
| GET | /export/users.csv | Export users as CSV | Admin |
| GET | /export/products.csv | Export products as CSV | Admin |
| POST | /notify | Send notification to user | Admin |
| POST | /migrate | Run database migrations | Admin |

---

## Frontend Pages

| Route | Component | Auth | Description |
|-------|-----------|------|-------------|
| `/` | page.tsx | No | Product feed with category filters |
| `/login` | login/page.tsx | No | Login with phone or username |
| `/register` | register/page.tsx | No | Register with role selection |
| `/post` | post/page.tsx | Seller+ | Create new listing |
| `/profile` | profile/page.tsx | Yes | Settings (Profile/Account tabs) |
| `/messages` | messages/page.tsx | Yes | Chat conversations |
| `/admin` | admin/page.tsx | Admin | Dashboard with tabs |

---

## Code Style Guidelines

### Python (Backend)
- **Imports:** stdlib → third-party → local (`from app.models import User`)
- **Line length:** Max 88 characters
- **Types:** Full type hints, `Optional[X]` not `X | None`
- **Collections:** `list[int]`, `dict[str, str]`
- **Enums:** Use `SQLEnum` from sqlalchemy

### TypeScript (Frontend)
- **Components:** Functional with hooks
- **Styling:** Tailwind CSS classes
- **State:** Zustand for auth, useState for local
- **API:** Axios with interceptors

### Error Handling
- **Backend:** `HTTPException` with appropriate codes (400, 401, 403, 404, 422)
- **Frontend:** User-facing error messages, no console.error in production

---

## Environment Variables

### Backend (.env) - Local Development
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key
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

# Admin seeding (only creates admin on first run if enabled)
CREATE_ADMIN=false
ADMIN_PHONE=254700000000
ADMIN_PASSWORD=admin123

# FluxPay M-Pesa Integration (get keys from FluxPay Settings > API Keys)
FLUXPAY_API_URL=https://fluxpay-api.onrender.com
FLUXPAY_API_KEY=fpk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FLUXPAY_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FLUXPAY_WEBHOOK_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FLUXPAY_BUSINESS_SHORTCODE=1234567
FLUXPAY_CALLBACK_URL=https://anything-marketplace-api.onrender.com/api/v1/webhooks/fluxpay
MPESA_PASSKEY=your_mpesa_passkey_here
MPESA_ENV=sandbox
```

### Backend (.env) - Production (Render)
```
DATABASE_URL=postgresql://user:pass@ep-xxx.eu-west-2.aws.neon.tech/neondb?sslmode=require
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
SECRET_KEY=random_32_char_string
DEBUG=false
CORS_ORIGINS=["https://anything-marketplace-web.onrender.com"]
REDIS_HOST=
STORAGE_TYPE=cloudinary
CREATE_ADMIN=false
```

### Frontend (.env.local) - Local Development
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Frontend - Production (Render)
```
NEXT_PUBLIC_API_URL=https://anything-marketplace-api.onrender.com
```

---

## Common Patterns

### Creating a new backend endpoint:
1. Define schema in `app/schemas/schemas.py`
2. Add model in `app/models/models.py` (if new)
3. Add route in `app/api/v1/`
4. Register router in `app/main.py`

### Creating a new frontend page:
1. Create `app/{route}/page.tsx`
2. Use existing components or create new in `components/`
3. Add API calls in `lib/api.ts` if needed
4. Update types in `types/index.ts` if needed

### Auth-protected route:
```python
@router.get("/me")
def read_current_user(
    current_user: User = Depends(get_current_active_user)
):
    return current_user
```

### Frontend auth check:
```typescript
const { isAuthenticated, user } = useAuthStore();
if (!isAuthenticated) router.push('/login');
```

---

## Image Handling

### Backend Compression
- Products: max 1200px width, JPEG quality 80
- Profiles: max 400px width, JPEG quality 85
- Convert PNG/GIF/WebP to JPEG
- Remove transparency by adding white background

### Frontend Compression
- Client-side canvas compression before upload
- Reduces upload size and improves UX

---

## Theming

- **Provider:** `ThemeProvider` in `context/theme.tsx`
- **Storage:** localStorage key `theme`
- **Default:** Respects `prefers-color-scheme`
- **Toggle:** Sun/Moon icon in Navbar

---

## Notes for AI Agents

1. **Always verify with tests** - don't assume code works
2. **Check PLANS.md** - follow the planned order if exists
3. **Handle errors gracefully** - return proper HTTP codes
4. **No placeholders** - implement complete, working code
5. **No hardcoded secrets** - use environment variables
6. **Frontend runs on :3000, Backend on :8000**
7. **Seller verification flow** - Sellers must be verified by admin before posting. WhatsApp links include phone numbers for easy contact.
8. **Messaging read receipts** - Messages show ✓ (sent) and ✓✓ (read) like WhatsApp. `is_delivered` field tracks delivery status.
9. **Auto-migration** - `run_migrations()` in `main.py` runs on startup to add missing columns and clean invalid data.