from typing import Optional
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Dependency / accessor for async Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = aioredis.from_url(
            settings.REDIS_URL, 
            encoding="utf-8", 
            decode_responses=True
        )
    return redis_client


async def close_redis():
    """Close Redis connection pool on app shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None