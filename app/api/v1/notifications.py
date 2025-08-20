from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.models import User
from app.core.security import get_current_active_user
from app.services.notifications import notification_service

router = APIRouter()

@router.get("/")
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user)
):
    """Get user notifications."""
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=current_user.id,
            limit=limit,
            offset=skip,
            unread_only=unread_only
        )
        return {"notifications": notifications}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Mark a notification as read."""
    try:
        success = await notification_service.mark_notification_read(
            notification_id=notification_id,
            user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.post("/mark-all-read")
async def mark_all_notifications_read(current_user: User = Depends(get_current_active_user)):
    """Mark all notifications as read for the current user."""
    try:
        count = await notification_service.mark_all_notifications_read(user_id=current_user.id)
        return {"message": f"Marked {count} notifications as read"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Delete a notification."""
    try:
        success = await notification_service.delete_notification(
            notification_id=notification_id,
            user_id=current_user.id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

@router.get("/stats")
async def get_notification_stats(current_user: User = Depends(get_current_active_user)):
    """Get notification statistics for the current user."""
    try:
        stats = await notification_service.get_notification_stats(user_id=current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification stats: {str(e)}"
        )

@router.post("/create")
async def create_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    current_user: User = Depends(get_current_active_user)
):
    """Create a new notification (for testing or system use)."""
    try:
        notification = await notification_service.create_notification(
            user_id=current_user.id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        return {"message": "Notification created successfully", "notification": notification}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )
