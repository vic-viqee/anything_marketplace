from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.products import router as products_router
from app.api.v1.chat import router as chat_router
from app.api.v1.nudge import router as nudge_router
from app.api.v1.ratings import router as ratings_router
from app.api.v1.admin import router as admin_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.tickets import router as tickets_router
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await redis_client.connect()
    except Exception:
        pass

    yield

    try:
        await redis_client.disconnect()
    except Exception:
        pass


Base.metadata.create_all(bind=engine)

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


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
app.include_router(ws_router)


@app.get("/")
def root():
    return {"message": "Anything Marketplace API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
