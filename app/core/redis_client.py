"""
Redis async connection pool for ATLAS-OPS.
Used for idempotency keys, circuit breaker state, and gateway simulation flags.
"""
from typing import AsyncGenerator

import redis.asyncio as aioredis

from app.core.config import get_settings

settings = get_settings()

# Global connection pool — created once at startup
_redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialise the Redis connection pool. Call at app startup."""
    import asyncio
    global _redis_pool
    from app.core.logging import get_logger
    logger = get_logger(__name__)

    pool = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=50,
    )

    # Added setup connection test with retries
    retries = 3
    connected = False
    for attempt in range(1, retries + 1):
        try:
            await pool.ping()
            connected = True
            break
        except Exception as e:
            if attempt < retries:
                await asyncio.sleep(1)
            else:
                logger.warning("Redis connection failed. Running without Redis caching. Error: %s", str(e))
    
    if connected:
        _redis_pool = pool


async def close_redis() -> None:
    """Gracefully close the Redis pool. Call at app shutdown."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


def get_redis_pool() -> aioredis.Redis:
    """Return the global Redis pool (must be initialised first)."""
    if _redis_pool is None:
        raise RuntimeError("Redis pool not initialised. Call init_redis() at startup.")
    return _redis_pool


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency: yields the shared Redis pool."""
    yield get_redis_pool()
