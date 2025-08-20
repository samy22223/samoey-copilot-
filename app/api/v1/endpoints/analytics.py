from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models import User, File, Notification, AnalyticsEvent
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.schemas.analytics import (
    AnalyticsResponse,
    UserStatsResponse,
    FileStatsResponse,
    SystemStatsResponse,
    TimeSeriesData
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get user statistics
        user_stats = await _get_user_stats(db, start_date, end_date)

        # Get file statistics
        file_stats = await _get_file_stats(db, start_date, end_date)

        # Get system statistics
        system_stats = await _get_system_stats(db, start_date, end_date)

        # Get time series data
        time_series = await _get_time_series_data(db, start_date, end_date)

        return AnalyticsResponse(
            user_stats=user_stats,
            file_stats=file_stats,
            system_stats=system_stats,
            time_series=time_series,
            period_days=days,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error generating dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")

@router.get("/users", response_model=UserStatsResponse)
async def get_user_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_user_stats(db, start_date, end_date)

@router.get("/files", response_model=FileStatsResponse)
async def get_file_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_file_stats(db, start_date, end_date)

@router.get("/system", response_model=SystemStatsResponse)
async def get_system_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_system_stats(db, start_date, end_date)

@router.get("/timeseries")
async def get_time_series_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    interval: str = Query("daily", description="Data interval: hourly, daily, weekly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get time series analytics data."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_time_series_data(db, start_date, end_date, interval)

@router.post("/event")
async def track_analytics_event(
    event_type: str,
    event_data: Dict[str, Any],
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Track an analytics event."""
    try:
        # Use current user ID if not provided
        if user_id is None:
            user_id = current_user.id

        analytics_event = AnalyticsEvent(
            event_type=event_type,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id,
            ip_address=current_user.last_login_ip,  # This should be captured from request
            user_agent=current_user.last_login_user_agent,  # This should be captured from request
            timestamp=datetime.utcnow()
        )

        db.add(analytics_event)
        db.commit()

        return {"message": "Event tracked successfully", "event_id": analytics_event.id}

    except Exception as e:
        logger.error(f"Error tracking analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track event")

@router.get("/events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics events with filtering."""
    if not current_user.is_superuser:
        # Regular users can only see their own events
        user_id = current_user.id

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.timestamp <= end_date
    )

    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)

    if user_id:
        query = query.filter(AnalyticsEvent.user_id == user_id)

    events = query.order_by(AnalyticsEvent.timestamp.desc()).limit(limit).all()
    return [{"id": event.id, "type": event.event_type, "data": event.event_data, "timestamp": event.timestamp} for event in events]

async def _get_user_stats(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get user statistics."""
    try:
        # Total users
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()

        # New users in period
        new_users = db.query(User).filter(
            User.created_at >= start_date,
            User.created_at <= end_date
        ).count()

        # Users by role
        users_by_role = db.query(
            User.role,
            db.func.count(User.id).label('count')
        ).group_by(User.role).all()

        # User activity (logins)
        from app.models import UserSession
        active_sessions = db.query(UserSession).filter(
            UserSession.created_at >= start_date,
            UserSession.created_at <= end_date
        ).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_period": new_users,
            "users_by_role": [{"role": role.role, "count": role.count} for role in users_by_role],
            "active_sessions_period": active_sessions,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return {}

async def _get_file_stats(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get file statistics."""
    try:
        # Total files
        total_files = db.query(File).count()

        # Files uploaded in period
        new_files = db.query(File).filter(
            File.created_at >= start_date,
            File.created_at <= end_date
        ).count()

        # Total storage used
        total_size = db.query(db.func.sum(File.file_size)).scalar() or 0

        # Files by content type
        files_by_type = db.query(
            File.content_type,
            db.func.count(File.id).label('count'),
            db.func.sum(File.file_size).label('total_size')
        ).group_by(File.content_type).all()

        # Files by user (top 10)
        files_by_user = db.query(
            File.uploaded_by,
            db.func.count(File.id).label('count'),
            db.func.sum(File.file_size).label('total_size')
        ).group_by(File.uploaded_by).order_by(db.func.count(File.id).desc()).limit(10).all()

        return {
            "total_files": total_files,
            "new_files_period": new_files,
            "total_storage_bytes": total_size,
            "total_storage_mb": round(total_size / (1024 * 1024), 2),
            "files_by_content_type": [
                {"type": ft.content_type, "count": ft.count, "total_size_bytes": ft.total_size}
                for ft in files_by_type
            ],
            "top_users_by_file_count": [
                {"user_id": fu.uploaded_by, "file_count": fu.count, "total_size_bytes": fu.total_size}
                for fu in files_by_user
            ],
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting file stats: {str(e)}")
        return {}

async def _get_system_stats(db: Session, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Get system statistics."""
    try:
        # Total notifications sent
        notifications_sent = db.query(Notification).filter(
            Notification.sent_at >= start_date,
            Notification.sent_at <= end_date
        ).count()

        # Analytics events in period
        total_events = db.query(AnalyticsEvent).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp <= end_date
        ).count()

        # Events by type
        events_by_type = db.query(
            AnalyticsEvent.event_type,
            db.func.count(AnalyticsEvent.id).label('count')
        ).filter(
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp <= end_date
        ).group_by(AnalyticsEvent.event_type).all()

        # System performance metrics (basic implementation)
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        return {
            "notifications_sent_period": notifications_sent,
            "total_events_period": total_events,
            "events_by_type": [
                {"event_type": et.event_type, "count": et.count}
                for et in events_by_type
            ],
            "system_performance": {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_percent": memory_usage,
                "disk_usage_percent": disk_usage
            },
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return {}

async def _get_time_series_data(db: Session, start_date: datetime, end_date: datetime, interval: str = "daily") -> List[Dict[str, Any]]:
    """Get time series analytics data."""
    try:
        from sqlalchemy import func, date

        time_series = []

        if interval == "hourly":
            # Group by hour
            time_series = db.query(
                func.date_trunc('hour', AnalyticsEvent.timestamp).label('period'),
                AnalyticsEvent.event_type,
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from app.db.session import get_db
from app.models import User, File, Notification, AnalyticsEvent
from app.core.security import get_current_active_user
from app.core.security_metrics import security_metrics
from app.schemas.analytics import (
    AnalyticsResponse,
    UserStatsResponse,
    FileStatsResponse,
    SystemStatsResponse,
    TimeSeriesData
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get user statistics
        user_stats = await _get_user_stats(db, start_date, end_date)

        # Get file statistics
        file_stats = await _get_file_stats(db, start_date, end_date)

        # Get system statistics
        system_stats = await _get_system_stats(db, start_date, end_date)

        # Get time series data
        time_series = await _get_time_series_data(db, start_date, end_date)

        return AnalyticsResponse(
            user_stats=user_stats,
            file_stats=file_stats,
            system_stats=system_stats,
            time_series=time_series,
            period_days=days,
            generated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error generating dashboard analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate analytics")

@router.get("/users", response_model=UserStatsResponse)
async def get_user_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_user_stats(db, start_date, end_date)

@router.get("/files", response_model=FileStatsResponse)
async def get_file_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get file-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_file_stats(db, start_date, end_date)

@router.get("/system", response_model=SystemStatsResponse)
async def get_system_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get system-related analytics."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_system_stats(db, start_date, end_date)

@router.get("/timeseries")
async def get_time_series_analytics(
    days: int = Query(30, description="Number of days to analyze"),
    interval: str = Query("daily", description="Data interval: hourly, daily, weekly"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get time series analytics data."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    return await _get_time_series_data(db, start_date, end_date, interval)

@router.post("/event")
async def track_analytics_event(
    event_type: str,
    event_data: Dict[str, Any],
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Track an analytics event."""
    try:
        # Use current user ID if not provided
        if user_id is None:
            user_id = current_user.id

        analytics_event = AnalyticsEvent(
            event_type=event_type,
            event_data=event_data,
            user_id=user_id,
            session_id=session_id,
            ip_address=current_user.last_login_ip,  # This should be captured from request
            user_agent=current_user.last_login_user_agent,  # This should be captured from request
            timestamp=datetime.utcnow()
        )

        db.add(analytics_event)
        db.commit()

        return {"message": "Event tracked successfully", "event_id": analytics_event.id}

    except Exception as e:
        logger.error(f"Error tracking analytics event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track event")

@router.get("/events")
async def get_analytics_events(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of events to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get analytics events with filtering."""
    if not current_user.is_superuser:
        # Regular users can only see their own events
        user_id = current_user.id

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    query = db.query(AnalyticsEvent).filter(
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.timestamp <= end_date
    )

    if event_type:
        query = query.filter(AnalyticsEvent.event_type == event_type)

    if user_id:
        query = query.filter(AnalyticsEvent.user_id == user_id)
