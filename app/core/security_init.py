from fastapi import FastAPI
from ..core.advanced_security import advanced_security
from ..core.ai_security import ai_security_manager
from ..core.security_monitor import security_monitor
from ..core.security_audit import security_audit_logger
from ..middleware.security import setup_security_headers
from ..middleware.ai_security import AISecurityMiddleware
from fastapi_limiter import FastAPILimiter
import redis.asyncio as redis
from ..core.security_settings import security_settings

async def initialize_security(app: FastAPI):
    """Initialize all security components"""
    # Initialize Redis connection
    redis_url = f"redis://{security_settings.REDIS_HOST}:{security_settings.REDIS_PORT}"
    redis_client = redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        db=security_settings.REDIS_SECURITY_DB
    )
    
    # Initialize rate limiting
    await FastAPILimiter.init(redis_client)
    
    # Initialize security components
    await advanced_security.initialize()
    await ai_security_manager.initialize()
    await security_monitor.initialize()
    
    # Setup security middleware
    setup_security_headers(app)
    app.add_middleware(AISecurityMiddleware)
    
    # Create required directories
    security_audit_logger._setup_logging()
    
    # Log initialization
    security_audit_logger.log_security_event(
        "system_startup",
        {"message": "Security system initialized"}
    )

async def cleanup_security():
    """Cleanup security components"""
    await advanced_security.close()
    await ai_security_manager.close()
    await security_monitor.close()
    
    # Log shutdown
    security_audit_logger.log_security_event(
        "system_shutdown",
        {"message": "Security system shutdown"}
    )
