import redis.asyncio as aioredis
from typing import AsyncGenerator
from config.settings import settings

# Create Redis pool
redis_pool = aioredis.ConnectionPool.from_url(
    str(settings.REDIS_URL),
    max_connections=10,
    decode_responses=True
)

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Get Redis client from pool."""
    client = aioredis.Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.close()

async def init_redis() -> None:
    """Initialize Redis connection and set up required keys."""
    redis = aioredis.Redis(connection_pool=redis_pool)
    try:
        # Test connection
        await redis.ping()
        
        # Initialize metrics if they don't exist
        metrics_key = f"{settings.METRICS_PREFIX}:metrics"
        if not await redis.exists(metrics_key):
            await redis.hset(metrics_key, mapping={
                "total_requests": 0,
                "active_users": 0,
                "error_count": 0,
                "last_error": "",
                "last_update": ""
            })
        
    except Exception as e:
        print(f"Redis initialization failed: {e}")
        raise
    finally:
        await redis.close()
