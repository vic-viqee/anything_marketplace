import redis.asyncio as redis
from typing import Optional, List
import json
from app.core.config import get_settings

settings = get_settings()


class RedisClient:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def get_cache(self, key: str) -> Optional[str]:
        if not self.redis:
            return None
        return await self.redis.get(key)

    async def set_cache(self, key: str, value: str, expire: int = 300):
        if not self.redis:
            return
        await self.redis.set(key, value, ex=expire)

    async def delete_cache(self, key: str):
        if not self.redis:
            return
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        if not self.redis:
            return
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    return redis_client


async def invalidate_feed_cache():
    await redis_client.delete_pattern("feed:*")
