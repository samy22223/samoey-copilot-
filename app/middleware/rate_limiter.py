from fastapi import FastAPI, Request, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from typing import Callable
import os

async def setup_rate_limiter(app: FastAPI):
    """Initialize the rate limiter with Redis."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_instance = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(redis_instance)

def rate_limit(
    calls: int = 100,
    period: int = 60
) -> Callable:
    """Rate limiting decorator for endpoints.
    
    Args:
        calls (int): Number of calls allowed
        period (int): Time period in seconds
    """
    return RateLimiter(times=calls, seconds=period)
