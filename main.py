"""Main FastAPI application entry point."""
import os
import asyncio
import logging
import platform
import psutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

# Import platform-specific configuration
from config.mobile import (
    get_platform_paths,
    get_mobile_config,
    get_ios_config,
    setup_platform_directories,
    MOBILE_OPTIMIZATIONS
)

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Import sync manager
from sync_manager import SyncManager

# Import configuration
from config.settings import settings

# Import database and models
from backend.db.session import engine, get_db, init_db, dispose_db

# Import middleware
from backend.middleware.logging import RequestLoggingMiddleware
from backend.middleware.security import SecurityMiddleware, setup_security_headers
from backend.middleware.error import ErrorHandlingMiddleware

# Import security components
from backend.security.orchestrator import SecurityOrchestrator
from backend.security.ai_security import AISecurityManager
from backend.security.advanced import AdvancedSecurity
from backend.security.metrics import SecurityMetrics
from backend.security.audit import SecurityAuditLogger

# Initialize sync service
sync_manager = SyncManager()

# Initialize security components
security_orchestrator = SecurityOrchestrator()
ai_security_manager = AISecurityManager()
advanced_security = AdvancedSecurity()
security_metrics = SecurityMetrics()
security_audit_logger = SecurityAuditLogger()
from models import User, Conversation, Message, UserRole, Base
from schemas import (
    UserCreate, UserResponse, MessageCreate, MessageResponse,
    ConversationCreate, ConversationResponse
)

# Import core components
from backend.core.logging import setup_logging, get_logger
from backend.core.redis import init_redis, get_redis
from backend.core.monitoring import init_monitoring
from backend.core.errors import setup_error_handlers

# Import routers
from backend.api import chat, auth, health

# Initialize logging
logger = setup_logging()

# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Configure middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    SecurityMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
    allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    max_body_size=settings.MAX_UPLOAD_SIZE
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Initialize application on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Set up platform-specific directories
    setup_platform_directories()
    
    # Initialize database
    await init_db()
    
    # Start WindSurf Cascade sync service
    asyncio.create_task(sync_manager.start_sync_service())
    
    # Apply mobile optimizations if client is mobile
    if settings.ENABLE_MOBILE_OPTIMIZATIONS:
        app.mobile_config = get_mobile_config()
        app.ios_config = get_ios_config()
        
    # Initialize security components
    await security_orchestrator.initialize()
    await ai_security_manager.initialize()
    await advanced_security.initialize()
    
    logger.info("Application startup complete")

# Shutdown event handler
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close database connections
        dispose_db()
        logger.info("Database connections closed")
        
        # Close Redis connections
        redis = await anext(get_redis())
        await redis.close()
        logger.info("Redis connections closed")
        
        # Cleanup security components
        await security_orchestrator.close()
        await advanced_security.close()
        await security_metrics.stop()
        await security_audit_logger.stop()
        
        # Stop sync service
        await sync_manager.stop()
        logger.info("WindSurf Cascade sync service stopped")
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
        raise
