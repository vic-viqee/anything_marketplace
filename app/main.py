from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.database import engine, Base
from sqlalchemy import text
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.chat import router as chat_router
from app.api.v1.nudge import router as nudge_router
from app.api.v1.ratings import router as ratings_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.reports import router as reports_router
from app.api.v1.websocket import router as ws_router
from app.services.redis_service import redis_client

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded

    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False


settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


def run_migrations():
    """Add missing columns to existing tables."""
    migrations = [
        ("users", "subscription_tier", "VARCHAR(20) DEFAULT 'free'"),
        ("users", "subscription_started_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "subscription_expires_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "featured_listings_used_this_month", "INTEGER DEFAULT 0"),
        ("users", "featured_listings_reset_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "kyc_status", "VARCHAR(20) DEFAULT 'none'"),
        ("users", "kyc_id_number", "VARCHAR(50)"),
        ("users", "kyc_id_front_url", "VARCHAR(500)"),
        ("users", "kyc_selfie_url", "VARCHAR(500)"),
        ("users", "kyc_submitted_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "kyc_reviewed_at", "TIMESTAMP WITH TIME ZONE"),
        ("users", "kyc_rejection_reason", "TEXT"),
        ("users", "is_suspended", "BOOLEAN DEFAULT FALSE"),
        ("users", "suspension_reason", "TEXT"),
        ("products", "is_featured", "BOOLEAN DEFAULT FALSE"),
        ("products", "featured_until", "TIMESTAMP WITH TIME ZONE"),
        ("products", "featured_by_admin", "BOOLEAN DEFAULT FALSE"),
    ]

    try:
        with engine.connect() as conn:
            for table, column, col_type in migrations:
                try:
                    result = conn.execute(
                        text(f"""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = '{table}' AND column_name = '{column}'
                    """)
                    )
                    if result.fetchone() is None:
                        conn.execute(
                            text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                        )
                        print(f"Migration: Added column {column} to {table}")
                except Exception as e:
                    print(f"Migration error for {column}: {e}")

            # Create reports table
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables WHERE table_name = 'reports'"
                )
            )
            if result.fetchone() is None:
                conn.execute(
                    text("""
                    CREATE TABLE reports (
                        id SERIAL PRIMARY KEY,
                        reporter_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        reported_user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        reported_product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
                        reason VARCHAR(50) NOT NULL,
                        description TEXT,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE
                    )
                """)
                )
                print("Migration: Created reports table")

            conn.commit()
    except Exception as e:
        print(f"Migration error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.connect()
    except Exception:
        pass

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:
        pass

    try:
        run_migrations()
    except Exception:
        pass

    try:
        seed_default_admin()
    except Exception:
        pass

    yield

    try:
        await redis_client.disconnect()
    except Exception:
        pass


def seed_default_admin():
    if not settings.CREATE_ADMIN:
        return
    from sqlalchemy.orm import Session
    from app.models.models import User, UserRole
    from app.services.auth_service import get_password_hash

    with Session(engine) as db:
        admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
        if admin is None:
            hashed = get_password_hash(settings.ADMIN_PASSWORD)
            new_admin = User(
                phone=settings.ADMIN_PHONE,
                username="admin",
                hashed_password=hashed,
                role=UserRole.ADMIN,
            )
            db.add(new_admin)
            db.commit()
            print("Default admin account created")


app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

if SLOWAPI_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT]
    )
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )


origins = settings.parsed_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(chat_router)
app.include_router(nudge_router)
app.include_router(ratings_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(tickets_router)
app.include_router(reports_router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {"message": "Anything Marketplace API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
