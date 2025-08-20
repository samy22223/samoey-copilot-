from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.core.redis import get_redis

router = APIRouter()


@router.get("/")
async def health_check(
    db: Session = Depends(get_db),
    redis=Depends(get_redis)
):
    """
    Comprehensive health check endpoint.
    Checks database, Redis, and overall application status.
    """
    health_status = {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "checks": {}
    }

    # Check database
    try:
        # Try to execute a simple query
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful"
        }
    except Exception as e:
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }
        health_status["status"] = "degraded"

    # Check AI services (if configured)
    if settings.HUGGINGFACE_TOKEN or settings.OPENAI_API_KEY:
        health_status["checks"]["ai_services"] = {
            "status": "configured",
            "message": "AI services configured"
        }
    else:
        health_status["checks"]["ai_services"] = {
            "status": "not_configured",
            "message": "AI services not configured"
        }

    return health_status


@router.get("/simple")
async def simple_health_check():
    """
    Simple health check for load balancers.
    Returns minimal information for quick checks.
    """
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    Indicates if the service is ready to accept traffic.
    """
    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }


@router.get("/live")
async def liveness_check():
    """
    Liveness check endpoint.
    Indicates if the service is running.
    """
    return {
        "status": "alive",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }
