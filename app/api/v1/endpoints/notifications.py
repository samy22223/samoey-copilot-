from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, Notification
from app.schemas.notification import NotificationCreate, NotificationUpdate, NotificationResponse
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.notification import notification_service
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new notification."""
    try:
        # Create notification
        db_notification = Notification(
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            target_user_id=notification.target_user_id,
            target_role=notification.target_role,
            is_global=notification.is_global,
            data=notification.data or {},
            created_by=current_user.id,
            expires_at=notification.expires_at
        )

        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        # Send notification in background
        background_tasks.add_task(
            notification_service.send_notification,
            db_notification.id
        )

        # Log security event
        security_metrics.record_security_event("notification_created", "info", {
            "user_id": current_user.id,
            "notification_id": db_notification.id,
            "type": notification.notification_type,
            "priority": notification.priority
        })

        return db_notification

    except Exception as e:
        logger.error(f"Error creating notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create notification")

@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    skip: int = 0,
    limit: int = 100,
    notification_type: Optional[str] = Query(None, description="Filter by notification type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    search: Optional[str] = Query(None, description="Search in title or message"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List notifications for current user."""
    query = db.query(Notification)

    # Filter for user-specific notifications or global notifications
    query = query.filter(
        (Notification.target_user_id == current_user.id) |
        (Notification.is_global == True) |
        (Notification.target_role == current_user.role)
    )

    # Filter by type
    if notification_type:
        query = query.filter(Notification.notification_type == notification_type)

    # Filter by priority
    if priority:
        query = query.filter(Notification.priority == priority)

    # Filter by read status
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    # Search in title or message
    if search:
        query = query.filter(
            (Notification.title.ilike(f"%{search}%")) |
            (Notification.message.ilike(f"%{search}%"))
        )

    # Exclude expired notifications
    now = datetime.utcnow()
    query = query.filter(
        (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
    )

    notifications = query.order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()
    return notifications

@router.get("/unread/count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread notifications for current user."""
    now = datetime.utcnow()

    unread_count = db.query(Notification).filter(
        (Notification.target_user_id == current_user.id) |
        (Notification.is_global == True) |
        (Notification.target_role == current_user.role)
    ).filter(
        Notification.is_read == False
    ).filter(
        (Notification.expires_at.is_(None)) | (Notification.expires_at > now)
    ).count()

    return {"unread_count": unread_count}

@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific notification."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check permissions
    if (notification.target_user_id != current_user.id and
        not notification.is_global and
        notification.target_role != current_user.role and
        not current_user.is_superuser):
        raise HTTPException(status_code=403, detail="Access denied")

    return notification

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark notification as read."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check permissions
    if (notification.target_user_id != current_user.id and
        not notification.is_global and
        notification.target_role != current_user.role and
        not current_user.is_superuser):
        raise HTTPException(status_code=403, detail="Access denied")

    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)

    return notification

@router.put("/mark-all-read")
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark all notifications as read for current user."""
    notifications = db.query(Notification).filter(
        (Notification.target_user_id == current_user.id) |
        (Notification.is_global == True) |
        (Notification.target_role == current_user.role)
    ).filter(
        Notification.is_read == False
    ).all()

    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()

    db.commit()

    return {"message": f"Marked {len(notifications)} notifications as read"}

@router.put("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: int,
    notification_update: NotificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update notification."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check permissions
    if notification.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    for field, value in notification_update.dict(exclude_unset=True).items():
        setattr(notification, field, value)

    notification.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(notification)

    return notification

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete notification."""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    # Check permissions
    if notification.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(notification)
    db.commit()

    # Log security event
    security_metrics.record_security_event("notification_deleted", "info", {
        "user_id": current_user.id,
        "notification_id": notification_id
    })

    return None

@router.post("/broadcast")
async def broadcast_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Broadcast notification to all users."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        # Create global notification
        db_notification = Notification(
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            is_global=True,
            data=notification.data or {},
            created_by=current_user.id,
            expires_at=notification.expires_at
        )

        db.add(db_notification)
        db.commit()
        db.refresh(db_notification)

        # Send broadcast notification in background
        background_tasks.add_task(
            notification_service.broadcast_notification,
            db_notification.id
        )

        # Log security event
        security_metrics.record_security_event("notification_broadcast", "info", {
            "user_id": current_user.id,
            "notification_id": db_notification.id,
            "type": notification.notification_type
        })

        return db_notification

    except Exception as e:
