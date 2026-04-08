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
- Post ads with images (auto-compressed to 1200px max)
- Product approval system (admin moderates before public)
- Built-in P2P chat messaging
- In-app notifications (product approved/rejected)
- Mark items as sold
- User ratings (1-5 stars)
- User profiles with photo, username, password management
- Dark/light mode theming
- Product detail page with seller info
- Contact seller via inbuilt chat or WhatsApp

### User Roles
- **Customer**: Browse, message sellers, rate after purchase
- **Seller**: Customer + post listings
- **Admin**: All abilities + approve/reject products, manage users, view analytics

---

## Technical Stack

### Backend
- **FastAPI** - Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching for feed endpoints
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **JWT** - Token-based auth
- **Pillow** - Image compression
- **Passlib** - Password hashing

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
│       └── notifications.py # In-app notifications
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
│   └── redis_service.py   # Redis caching
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
- `profile_image` (nullable)
- `role` (enum: customer/seller/admin)
- `is_active` (boolean)
- `created_at`, `updated_at`

### Products Table
- `id` (PK)
- `title`, `description`, `price`
- `image_url` (nullable)
- `status` (enum: available/sold/archived)
- `is_approved` (boolean)
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
- `content`, `is_read`
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
| GET | /feed | Paginated approved listings | No |
| GET | / | All approved listings | No |
| GET | /{id} | Single product | No |
| POST | / | Create listing | Seller+ |
| PUT | /{id} | Update listing | Owner |
| DELETE | /{id} | Delete listing | Owner |
| POST | /{id}/mark-sold | Mark as sold | Owner |
| GET | /categories | List categories | No |
| POST | /{id}/ratings | Rate seller | Customer |
| GET | /users/{id}/ratings | Get user ratings | No |

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

### Admin (`/api/v1/admin`)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /analytics | Dashboard stats | Admin |
| GET | /products/pending | Pending products | Admin |
| POST | /products/{id}/approve | Approve product | Admin |
| POST | /products/{id}/reject | Reject product | Admin |
| GET | /users | List users | Admin |
| PATCH | /users/{id}/role | Update role | Admin |
| DELETE | /users/{id} | Delete user | Admin |
| DELETE | /products/{id} | Delete product | Admin |

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

### Backend (.env)
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/marketplace
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
UPLOAD_DIR=./uploads
ADMIN_PHONE=+254700000010
ADMIN_PASSWORD=password
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
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

## Default Test Accounts

| Phone | Password | Role |
|-------|----------|------|
| +254700000010 | password | Admin |
| +254700000011 | password | Seller |
| +254700000002 | test123 | Customer |

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
7. **Product detail page NOT implemented** - ProductCard links to `/product/{id}` but route doesn't exist yet
8. **Login accepts phone OR username** - auto-detects format
9. **Admin cannot post like seller** - role check in backend, but admin sees "Post Ad" link (intentional)
10. **Build both frontend and backend** - verify changes work end-to-end
