from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime

from ..core.monitoring import system_monitor
from ..core.redis import get_redis
from ..core.database import get_db

router = APIRouter()

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint"""
    # Get system stats
    stats = system_monitor.get_system_stats()
    
    # Check Redis connection
    redis = await get_redis()
    redis_ok = await redis.ping()
    
    # Check database connection
    db = next(get_db())
    db_ok = db.is_active
    
    return {
        "status": "healthy" if all([redis_ok, db_ok]) else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "redis": "up" if redis_ok else "down",
            "database": "up" if db_ok else "down"
        },
        "system": stats
    }

@router.get("/metrics/summary")
async def metrics_summary() -> Dict[str, Any]:
    """Get summary of system metrics"""
    # Get system stats
    stats = system_monitor.get_system_stats()
    
    # Get request metrics from Prometheus
    metrics = {
        "requests": {
            "total": system_monitor.REQUEST_COUNT._value.sum(),
            "active": system_monitor.ACTIVE_REQUESTS._value.get(),
            "errors": system_monitor.ERROR_COUNT._value.sum()
        },
        "performance": {
            "latency_avg": system_monitor.REQUEST_LATENCY._sum.get() / 
                          max(system_monitor.REQUEST_LATENCY._count.get(), 1)
        },
        "system": stats
    }
    
    return metrics
