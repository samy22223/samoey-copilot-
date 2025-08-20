from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User, Webhook, WebhookLog
from app.schemas.webhook import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookLogResponse
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.services.webhook import webhook_service
from datetime import datetime, timedelta
import logging
import secrets

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    webhook: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new webhook."""
    try:
        # Generate secret if not provided
        if not webhook.secret:
            webhook.secret = secrets.token_urlsafe(32)

        # Create webhook
        db_webhook = Webhook(
            name=webhook.name,
            url=webhook.url,
            secret=webhook.secret,
            events=webhook.events,
            is_active=webhook.is_active,
            description=webhook.description,
            custom_headers=webhook.custom_headers or {},
            retry_count=webhook.retry_count,
            timeout_seconds=webhook.timeout_seconds,
            created_by=current_user.id
        )

        db.add(db_webhook)
        db.commit()
        db.refresh(db_webhook)

        # Log security event
        security_metrics.record_security_event("webhook_created", "info", {
            "user_id": current_user.id,
            "webhook_id": db_webhook.id,
            "webhook_name": webhook.name,
            "events": webhook.events
        })

        return db_webhook

    except Exception as e:
        logger.error(f"Error creating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create webhook")

@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List webhooks for current user."""
    query = db.query(Webhook).filter(Webhook.created_by == current_user.id)

    # Filter by active status
    if is_active is not None:
        query = query.filter(Webhook.is_active == is_active)

    # Filter by event type
    if event_type:
        query = query.filter(Webhook.events.contains([event_type]))

    # Search in name or description
    if search:
        query = query.filter(
            (Webhook.name.ilike(f"%{search}%")) |
            (Webhook.description.ilike(f"%{search}%"))
        )

    webhooks = query.order_by(Webhook.created_at.desc()).offset(skip).limit(limit).all()
    return webhooks

@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    return webhook

@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_update: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Update fields
    for field, value in webhook_update.dict(exclude_unset=True).items():
        setattr(webhook, field, value)

    webhook.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(webhook)

    return webhook

@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete webhook."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete(webhook)
    db.commit()

    # Log security event
    security_metrics.record_security_event("webhook_deleted", "info", {
        "user_id": current_user.id,
        "webhook_id": webhook_id
    })

    return None

@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    test_data: dict = {},
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Test webhook by sending a test event."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Create test event data
    event_data = {
        "event": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "data": test_data,
        "webhook_id": webhook_id,
        "test": True
    }

    # Send test webhook in background
    background_tasks.add_task(
        webhook_service.send_webhook,
        webhook.id,
        event_data,
        is_test=True
    )

    return {"message": "Test webhook sent", "event_data": event_data}

@router.get("/{webhook_id}/logs", response_model=List[WebhookLogResponse])
async def get_webhook_logs(
    webhook_id: int,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, description="Filter by status: success, failed"),
    days: int = Query(30, description="Number of days to look back"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get webhook delivery logs."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.created_at >= start_date,
        WebhookLog.created_at <= end_date
    )

    if status:
        query = query.filter(WebhookLog.status == status)

    logs = query.order_by(WebhookLog.created_at.desc()).offset(skip).limit(limit).all()
    return logs

@router.post("/{webhook_id}/rotate-secret")
async def rotate_webhook_secret(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Rotate webhook secret."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Generate new secret
    new_secret = secrets.token_urlsafe(32)
    old_secret = webhook.secret

    webhook.secret = new_secret
    webhook.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(webhook)

    # Log security event
    security_metrics.record_security_event("webhook_secret_rotated", "info", {
        "user_id": current_user.id,
        "webhook_id": webhook_id
    })

    return {
        "message": "Webhook secret rotated successfully",
        "new_secret": new_secret,
        "webhook_id": webhook_id
    }

@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: int,
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get webhook delivery statistics."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
    if webhook is None:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Check permissions
    if webhook.created_by != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Get delivery statistics
    total_deliveries = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.created_at >= start_date,
        WebhookLog.created_at <= end_date
    ).count()

    successful_deliveries = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.status == "success",
        WebhookLog.created_at >= start_date,
        WebhookLog.created_at <= end_date
    ).count()

    failed_deliveries = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.status == "failed",
        WebhookLog.created_at >= start_date,
        WebhookLog.created_at <= end_date
    ).count()

    # Calculate average response time
    successful_logs = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.status == "success",
        WebhookLog.response_time.isnot(None),
        WebhookLog.created_at >= start_date,
        WebhookLog.created_at <= end_date
    ).all()

    avg_response_time = None
    if successful_logs:
        avg_response_time = sum(log.response_time for log in successful_logs) / len(successful_logs)

    # Get recent activity (last 24 hours)
    recent_start = datetime.utcnow() - timedelta(hours=24)
    recent_deliveries = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id,
        WebhookLog.created_at >= recent_start
    ).count()

    return {
        "webhook_id": webhook_id,
        "period_days": days,
        "total_deliveries": total_deliveries,
        "successful_deliveries": successful_deliveries,
        "failed_deliveries": failed_deliveries,
        "success_rate": round((successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0, 2),
        "average_response_time_ms": round(avg_response_time, 2) if avg_response_time else None,
        "recent_deliveries_24h": recent_deliveries,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat()
    }

@router.post("/trigger/{event_type}")
async def trigger_webhooks(
    event_type: str,
    event_data: dict,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Trigger all webhooks that listen to a specific event type."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Find all active webhooks that listen to this event type
    webhooks = db.query(Webhook).filter(
        Webhook.is_active == True,
        Webhook.events.contains([event_type])
    ).all()

    if not webhooks:
        return {"message": "No webhooks found for this event type", "webhooks_triggered": 0}

    # Trigger webhooks in background
    for webhook in webhooks:
        background_tasks.add_task(
            webhook_service.send_webhook,
            webhook.id,
            event_data
        )

    return {
        "message": f"Triggered {len(webhooks)} webhooks for event: {event_type}",
        "webhooks_triggered": len(webhooks),
        "event_type": event_type,
        "event_data": event_data
    }

@router.get("/events")
async def get_available_events():
    """Get list of available webhook events."""
    events = [
        "user.created",
        "user.updated",
        "user.deleted",
        "file.uploaded",
        "file.updated",
        "file.deleted",
        "notification.sent",
        "notification.failed",
        "system.backup.completed",
        "system.backup.failed",
        "system.maintenance.started",
        "system.maintenance.completed",
        "security.event",
        "analytics.event"
    ]

    return {
        "available_events": events,
        "description": "Webhooks can be configured to listen to these event types"
    }
