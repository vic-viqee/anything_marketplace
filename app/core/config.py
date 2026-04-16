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

    CORS_ORIGINS: str = ""

    # FluxPay Configuration
    FLUXPAY_API_URL: str = "https://fluxpay-api.onrender.com"
    FLUXPAY_API_KEY: str = ""
    FLUXPAY_API_SECRET: str = ""
    FLUXPAY_WEBHOOK_SECRET: str = ""

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"
    RATE_LIMIT_ADMIN: str = "200/minute"

    CREATE_ADMIN: bool = False
    ADMIN_PHONE: str = "254700000000"
    ADMIN_PASSWORD: str = "admin123"

    TIER_PRICES: str = "free:0,basic:200,standard:500,premium:1000"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def parsed_cors_origins(self) -> list[str]:
        # Default origins
        defaults = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://anything-marketplace-web.onrender.com",
        ]

        if not self.CORS_ORIGINS:
            return defaults

        try:
            # Try JSON parsing first
            parsed = json.loads(self.CORS_ORIGINS)
            if isinstance(parsed, list):
                return parsed + defaults
            return defaults
        except (json.JSONDecodeError, TypeError):
            pass

        # Try comma-separated
        if "," in self.CORS_ORIGINS:
            return [o.strip() for o in self.CORS_ORIGINS.split(",")] + defaults

        return defaults

    def get_tier_price(self, tier: str) -> int:
        """Get price for a subscription tier"""
        tier_prices = {}
        for item in self.TIER_PRICES.split(","):
            if ":" in item:
                t, price = item.split(":")
                tier_prices[t.strip()] = int(price.strip())
        return tier_prices.get(tier, 0)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
