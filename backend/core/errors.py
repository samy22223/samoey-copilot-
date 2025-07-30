from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from typing import Any, Dict
from datetime import datetime
from backend.core.logging import get_logger

logger = get_logger(__name__)

class AppError(Exception):
    """Base application error."""
    def __init__(
        self,
        message: str,
        error_code: str = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Dict[str, Any] = None
    ):
        self.message = message
        self.error_code = error_code or "INTERNAL_ERROR"
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class ValidationError(AppError):
    """Validation error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )

class DatabaseError(AppError):
    """Database error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )

class AuthenticationError(AppError):
    """Authentication error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )

class AuthorizationError(AppError):
    """Authorization error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )

class NotFoundError(AppError):
    """Resource not found error."""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle application errors."""
    error_data = {
        "error": {
            "code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Log error
    logger.error(
        f"Application error: {exc.error_code} - {exc.message}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "details": exc.details
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_data
    )

async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors."""
    error_details = []
    for error in exc.errors():
        error_details.append({
            "location": error["loc"],
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_data = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": error_details,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Log error
    logger.warning(
        "Validation error",
        extra={
            "path": str(request.url),
            "method": request.method,
            "details": error_details
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_data
    )

async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle database errors."""
    error_data = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "Database operation failed",
            "details": {"error": str(exc)},
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Log error
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_data
    )

async def redis_error_handler(request: Request, exc: RedisError) -> JSONResponse:
    """Handle Redis errors."""
    error_data = {
        "error": {
            "code": "REDIS_ERROR",
            "message": "Cache operation failed",
            "details": {"error": str(exc)},
            "timestamp": datetime.now().isoformat()
        }
    }
    
    # Log error
    logger.error(
        f"Redis error: {str(exc)}",
        extra={
            "path": str(request.url),
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_data
    )

def setup_error_handlers(app):
    """Set up error handlers for the application."""
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(RedisError, redis_error_handler)
