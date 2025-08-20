from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
from app.models import User
from app.core.security import get_current_active_user
from app.services.notifications import notification_service
from app.core.logging import logger
from app.middleware.ratelimit import rate_limit
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

router = APIRouter()

# Enums for better type safety
class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"
    SYSTEM = "system"
    SECURITY = "security"

# Response Models
class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    data: dict
    created_at: datetime
    read: bool

class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    page: int
    limit: int

class NotificationStatsResponse(BaseModel):
    total: int
    unread: int
    read: int
    by_type: dict

class NotificationCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    type: NotificationType = Field(default=NotificationType.INFO)
    data: Optional[dict] = Field(default_factory=dict)

class NotificationCreateResponse(BaseModel):
    message: str
    notification: NotificationResponse

# Error handler decorator
def handle_api_errors(func):
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except PermissionError as e:
            logger.warning(f"Permission error in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred"
            )
    return wrapper

# Validation helpers
def validate_notification_id(notification_id: str) -> str:
    """Validate notification ID format."""
    if not notification_id or not notification_id.strip():
        raise ValueError("Notification ID is required")
    return notification_id.strip()

@router.get("/", response_model=NotificationListResponse)
@rate_limit(calls=200, period=60)
@handle_api_errors
@cache(expire=30)  # Cache for 30 seconds
async def get_notifications(
    skip: int = Query(0, ge=0, description="Number of notifications to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications to return"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications with pagination and caching."""
    logger.info(f"User {current_user.id} fetching notifications: skip={skip}, limit={limit}, unread_only={unread_only}")

    notifications = await notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=skip,
        unread_only=unread_only
    )

    # Get counts for stats
    total_count = await notification_service.get_user_notifications_count(user_id=current_user.id)
    unread_count = await notification_service.get_user_unread_notifications_count(user_id=current_user.id)

    return NotificationListResponse(
        notifications=notifications,
        total=total_count,
        unread_count=unread_count,
        page=skip // limit + 1,
        limit=limit
    )

@router.post("/{notification_id}/read")
@rate_limit(calls=100, period=60)
@handle_api_errors
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Mark a notification as read."""
    notification_id = validate_notification_id(notification_id)
    logger.info(f"User {current_user.id} marking notification as read: {notification_id}")

    success = await notification_service.mark_notification_read(
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    # Clear cache for this user's notifications
    await FastAPICache.clear(namespace=f"user_notifications_{current_user.id}")

    logger.info(f"Notification marked as read: {notification_id}")
    return {"message": "Notification marked as read"}

@router.post("/mark-all-read")
@rate_limit(calls=10, period=60)  # Limit this operation
@handle_api_errors
async def mark_all_notifications_read(current_user: User = Depends(get_current_active_user)):
    """Mark all notifications as read for the current user."""
    logger.info(f"User {current_user.id} marking all notifications as read")

    count = await notification_service.mark_all_notifications_read(user_id=current_user.id)

    # Clear cache for this user's notifications
    await FastAPICache.clear(namespace=f"user_notifications_{current_user.id}")

    logger.info(f"Marked {count} notifications as read for user {current_user.id}")
    return {"message": f"Marked {count} notifications as read"}

@router.delete("/{notification_id}")
@rate_limit(calls=50, period=60)
@handle_api_errors
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification."""
    notification_id = validate_notification_id(notification_id)
    logger.info(f"User {current_user.id} deleting notification: {notification_id}")

    success = await notification_service.delete_notification(
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    # Clear cache for this user's notifications
    await FastAPICache.clear(namespace=f"user_notifications_{current_user.id}")

    logger.info(f"Notification deleted: {notification_id}")
    return {"message": "Notification deleted successfully"}

@router.get("/stats", response_model=NotificationStatsResponse)
@rate_limit(calls=60, period=60)
@handle_api_errors
@cache(expire=60)  # Cache for 1 minute
async def get_notification_stats(current_user: User = Depends(get_current_active_user)):
    """Get notification statistics for the current user."""
    logger.info(f"User {current_user.id} requesting notification stats")

    stats = await notification_service.get_notification_stats(user_id=current_user.id)

    return NotificationStatsResponse(
        total=stats["total"],
        unread=stats["unread"],
        read=stats["read"],
        by_type=stats["by_type"]
    )

@router.post("/create", response_model=NotificationCreateResponse)
@rate_limit(calls=20, period=60)
@handle_api_errors
async def create_notification(
    request: NotificationCreateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Create a new notification (for testing or system use)."""
    logger.info(f"User {current_user.id} creating notification: {request.title}")

    # Validate content length
    if len(request.title.strip()) == 0:
        raise ValueError("Title cannot be empty")
    if len(request.message.strip()) == 0:
        raise ValueError("Message cannot be empty")

    notification = await notification_service.create_notification(
        user_id=current_user.id,
        title=request.title.strip(),
        message=request.message.strip(),
        notification_type=request.type.value,
        data=request.data or {}
    )

    # Clear cache for this user's notifications
    await FastAPICache.clear(namespace=f"user_notifications_{current_user.id}")

    logger.info(f"Notification created: {notification.get('id')}")
    return NotificationCreateResponse(
        message="Notification created successfully",
        notification=NotificationResponse(**notification)
    )

@router.delete("/cleanup-old")
@rate_limit(calls=5, period=3600)  # 5 times per hour
@handle_api_errors
async def cleanup_old_notifications(
    days: int = Query(30, ge=1, le=365, description="Delete notifications older than N days"),
    current_user: User = Depends(get_current_active_user)
):
    """Clean up old notifications (optional maintenance endpoint)."""
    logger.info(f"User {current_user.id} cleaning up notifications older than {days} days")

    deleted_count = await notification_service.cleanup_old_notifications(
        user_id=current_user.id,
        days=days
    )

    # Clear cache for this user's notifications
    await FastAPICache.clear(namespace=f"user_notifications_{current_user.id}")

    logger.info(f"Cleaned up {deleted_count} old notifications for user {current_user.id}")
    return {"message": f"Cleaned up {deleted_count} old notifications"}
