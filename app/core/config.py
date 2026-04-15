from pydantic_settings import BaseSettings
from functools import lru_cache
import json


class Settings(BaseSettings):
    APP_NAME: str = "Anything Marketplace"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql://postgres@localhost:5432/marketplace"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    SECRET_KEY: str = "supersecretkey123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    MAX_IMAGE_WIDTH: int = 1200
    MAX_PROFILE_WIDTH: int = 400

    CORS_ORIGINS: str = '["http://localhost:3000","http://127.0.0.1:3000"]'

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_ADMIN: str = "200/minute"

    CREATE_ADMIN: bool = False
    ADMIN_PHONE: str = "254700000000"
    ADMIN_PASSWORD: str = "admin123"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def parsed_cors_origins(self) -> list[str]:
        try:
            return json.loads(self.CORS_ORIGINS)
        except (json.JSONDecodeError, TypeError):
            return ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
