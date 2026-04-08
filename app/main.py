from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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
from app.services.redis_service import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    try:
        await redis_client.connect()
    except Exception:
        pass

    yield

    await redis_client.disconnect()


settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

app.include_router(auth_router)
app.include_router(products_router)
app.include_router(chat_router)
app.include_router(nudge_router)
app.include_router(ratings_router)
app.include_router(admin_router)
app.include_router(notifications_router)
app.include_router(tickets_router)


@app.get("/")
def root():
    return {"message": "Anything Marketplace API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
