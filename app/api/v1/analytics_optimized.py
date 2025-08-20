from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
from app.models import User
from app.core.security import get_current_active_user
from app.services.analytics import analytics_service
from app.core.logging import logger
from app.middleware.ratelimit import rate_limit
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

router = APIRouter()

# Enums for better type safety
class AnalyticsPeriod(str, Enum):
    HOUR = "1h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"
    YEAR = "365d"

class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    USER_ACTION = "user_action"
    API_CALL = "api_call"
    ERROR = "error"
    PERFORMANCE = "performance"
    SECURITY = "security"

# Response Models
class UsageAnalyticsResponse(BaseModel):
    period: Dict[str, str]
    user_activity: Dict[str, Any]
    messaging: Dict[str, Any]
    file_operations: Dict[str, Any]
    api_usage: Dict[str, Any]
    ai_interactions: Dict[str, Any]

class PerformanceMetricsResponse(BaseModel):
    timestamp: datetime
    system: Dict[str, Any]
    process: Dict[str, Any]
    network: Dict[str, Any]
    response_times: Dict[str, Any]
    health: Dict[str, Any]

class UserAnalyticsResponse(BaseModel):
    user_id: str
    period: str
    activity_summary: Dict[str, Any]
    feature_usage: Dict[str, Any]
    engagement_metrics: Dict[str, Any]
    growth_trend: Dict[str, Any]

class SystemAnalyticsResponse(BaseModel):
    timestamp: datetime
    overview: Dict[str, Any]
    performance: Dict[str, Any]
    resource_usage: Dict[str, Any]
    top_features: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]

class RealtimeMetricsResponse(BaseModel):
    timestamp: datetime
    current: Dict[str, Any]
    performance: Dict[str, Any]
    health: Dict[str, Any]

class EventRecordRequest(BaseModel):
    event_type: EventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

class EventRecordResponse(BaseModel):
    message: str
    event_id: str

# Request validation models
class DateRangeRequest(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Start date for analytics range")
    end_date: Optional[datetime] = Field(None, description="End date for analytics range")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and 'start_date' in values and values['start_date']:
            if v <= values['start_date']:
                raise ValueError("End date must be after start date")
            if v - values['start_date'] > timedelta(days=365):
                raise ValueError("Date range cannot exceed 365 days")
        return v

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
def validate_days_param(days: int) -> int:
    """Validate days parameter."""
    if days < 1 or days > 365:
        raise ValueError("Days parameter must be between 1 and 365")
    return days

def validate_period_param(period: str) -> str:
    """Validate period parameter."""
    valid_periods = [p.value for p in AnalyticsPeriod]
    if period not in valid_periods:
        raise ValueError(f"Period must be one of: {', '.join(valid_periods)}")
    return period

@router.get("/usage", response_model=UsageAnalyticsResponse)
@rate_limit(calls=60, period=60)
@handle_api_errors
@cache(expire=300)  # Cache for 5 minutes
async def get_usage_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    period: Optional[str] = Query(None, description="Predefined period (1h, 24h, 7d, 30d, 90d, 365d)"),
    current_user: User = Depends(get_current_active_user)
):
    """Get usage analytics for the current user."""
    logger.info(f"User {current_user.id} requesting usage analytics")

    # Validate date range or period
    if period:
        period = validate_period_param(period)
        # Convert period to actual dates
        end_date = datetime.now()
        if period == "1h":
            start_date = end_date - timedelta(hours=1)
        elif period == "24h":
            start_date = end_date - timedelta(days=1)
        elif period == "7d":
            start_date = end_date - timedelta(days=7)
        elif period == "30d":
            start_date = end_date - timedelta(days=30)
        elif period == "90d":
            start_date = end_date - timedelta(days=90)
        elif period == "365d":
            start_date = end_date - timedelta(days=365)

    date_range = DateRangeRequest(start_date=start_date, end_date=end_date)

    analytics = await analytics_service.get_usage_analytics(
        user_id=current_user.id,
        start_date=date_range.start_date,
        end_date=date_range.end_date
    )

    return UsageAnalyticsResponse(**analytics)

@router.get("/performance", response_model=PerformanceMetricsResponse)
@rate_limit(calls=120, period=60)
@handle_api_errors
@cache(expire=60)  # Cache for 1 minute
async def get_performance_metrics(current_user: User = Depends(get_current_active_user)):
    """Get system performance metrics."""
    logger.info(f"User {current_user.id} requesting performance metrics")

    metrics = await analytics_service.get_performance_metrics()

    return PerformanceMetricsResponse(**metrics)

@router.get("/user", response_model=UserAnalyticsResponse)
@rate_limit(calls=30, period=60)
@handle_api_errors
@cache(expire=600)  # Cache for 10 minutes
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed analytics for the current user."""
    days = validate_days_param(days)
    logger.info(f"User {current_user.id} requesting user analytics for {days} days")

    analytics = await analytics_service.get_user_analytics(
        user_id=current_user.id,
        days=days
    )

    return UserAnalyticsResponse(**analytics)

@router.get("/system", response_model=SystemAnalyticsResponse)
@rate_limit(calls=30, period=60)
@handle_api_errors
@cache(expire=300)  # Cache for 5 minutes
async def get_system_analytics(current_user: User = Depends(get_current_active_user)):
    """Get system-wide analytics (admin only)."""
    logger.info(f"User {current_user.id} requesting system analytics")

    # In a real implementation, check if user is admin
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )

    analytics = await analytics_service.get_system_analytics()

    return SystemAnalyticsResponse(**analytics)

@router.get("/realtime", response_model=RealtimeMetricsResponse)
@rate_limit(calls=300, period=60)  # Higher limit for real-time data
@handle_api_errors
@cache(expire=10)  # Cache for 10 seconds only
async def get_real_time_metrics(current_user: User = Depends(get_current_active_user)):
    """Get real-time metrics for monitoring."""
    logger.info(f"User {current_user.id} requesting real-time metrics")

    metrics = await analytics_service.get_real_time_metrics()

    return RealtimeMetricsResponse(**metrics)

@router.post("/events", response_model=EventRecordResponse)
@rate_limit(calls=100, period=60)
@handle_api_errors
async def record_analytics_event(
    request: EventRecordRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Record an analytics event."""
    logger.info(f"User {current_user.id} recording event: {request.event_type}")

    # Validate event data
    if not request.data:
        request.data = {}

    # Add user context
    request.data['user_id'] = current_user.id
    if not request.session_id:
        request.session_id = f"user_{current_user.id}"

    success = await analytics_service.record_event(
        event_type=request.event_type.value,
        user_id=current_user.id,
        data=request.data,
        timestamp=request.timestamp or datetime.now()
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record event"
        )

    # Clear relevant caches
    await FastAPICache.clear(namespace=f"user_analytics_{current_user.id}")
    await FastAPICache.clear(namespace="realtime_metrics")

    logger.info(f"Event recorded successfully: {request.event_type}")
    return EventRecordResponse(
        message="Event recorded successfully",
        event_id=f"{request.event_type.value}_{int(datetime.now().timestamp())}"
    )

@router.get("/export")
@rate_limit(calls=10, period=3600)  # 10 exports per hour
@handle_api_errors
async def export_analytics(
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    start_date: Optional[datetime] = Query(None, description="Start date for export"),
    end_date: Optional[datetime] = Query(None, description="End date for export"),
    current_user: User = Depends(get_current_active_user)
):
    """Export analytics data."""
    logger.info(f"User {current_user.id} exporting analytics data in {format} format")

    date_range = DateRangeRequest(start_date=start_date, end_date=end_date)

    export_data = await analytics_service.export_analytics(
        user_id=current_user.id,
        format=format,
        start_date=date_range.start_date,
        end_date=date_range.end_date
    )

    logger.info(f"Analytics data exported successfully for user {current_user.id}")
    return export_data

@router.get("/dashboard")
@rate_limit(calls=60, period=60)
@handle_api_errors
@cache(expire=120)  # Cache for 2 minutes
async def get_dashboard_data(
    period: str = Query("7d", description="Time period for dashboard data"),
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive dashboard data."""
    period = validate_period_param(period)
    logger.info(f"User {current_user.id} requesting dashboard data for period: {period}")

    # Get multiple analytics data points in parallel
    dashboard_data = await analytics_service.get_dashboard_data(
        user_id=current_user.id,
        period=period
    )

    return dashboard_data

@router.delete("/cleanup")
@rate_limit(calls=5, period=3600)  # 5 cleanups per hour
@handle_api_errors
async def cleanup_old_analytics(
    days: int = Query(90, ge=30, le=730, description="Delete analytics data older than N days"),
    current_user: User = Depends(get_current_active_user)
):
    """Clean up old analytics data (admin only)."""
    logger.info(f"User {current_user.id} cleaning up analytics data older than {days} days")

    # Check admin permissions
    # if not current_user.is_admin:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Admin access required"
    #     )

    deleted_count = await analytics_service.cleanup_old_data(days=days)

    logger.info(f"Cleaned up {deleted_count} old analytics records")
    return {"message": f"Cleaned up {deleted_count} old analytics records"}
