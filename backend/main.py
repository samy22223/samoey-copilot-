import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.config import settings
from backend.api.v1.api import api_router
from backend.db.session import engine, Base
from backend.db.init_db import init_db
from backend.core.security_init import initialize_security, cleanup_security
from backend.core.security_settings import security_settings
from backend.core.security_metrics import security_metrics
from backend.core.security_monitor import security_monitor
from backend.core.security_audit import security_audit_logger

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Pinnacle Copilot - AI-Powered Development Assistant",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security initialization
@app.on_event("startup")
async def startup_event():
    """Initialize security components on startup"""
    try:
        await initialize_security(app)
        await security_metrics.initialize()
        logger.info("Security components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing security components: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup security components on shutdown"""
    try:
        await cleanup_security()
        await security_metrics.close()
        logger.info("Security components cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up security components: {str(e)}")

# Global exception handler for security events
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle and log all exceptions"""
    # Log security-relevant exceptions
    if isinstance(exc, (HTTPException, RequestValidationError)):
        security_audit_logger.log_security_event(
            "security_exception",
            {
                "path": str(request.url),
                "method": request.method,
                "client_ip": request.client.host,
                "exception_type": type(exc).__name__,
                "detail": str(exc)
            }
        )
    
    # Re-raise the exception for normal handling
    raise exc

# Security middleware setup
@app.middleware("http")
async def security_metrics_middleware(request: Request, call_next):
    """Collect security metrics for all requests"""
    try:
        response = await call_next(request)
        
        # Track successful requests
        security_metrics.SECURITY_METRICS['events'].labels(
            type="request_success"
        ).inc()
        
        return response
    except Exception as e:
        # Track failed requests
        security_metrics.SECURITY_METRICS['events'].labels(
            type="request_failure"
        ).inc()
        raise

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    # Initialize database with default data
    await init_db()
    logger.info("Database initialized")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down...")

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Pinnacle Copilot API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }
