from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime
from app.models import User
from app.core.security import get_current_active_user
from app.services.analytics import analytics_service

router = APIRouter()

@router.get("/usage")
async def get_usage_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Get usage analytics for the current user."""
    try:
        analytics = await analytics_service.get_usage_analytics(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage analytics: {str(e)}"
        )

@router.get("/performance")
async def get_performance_metrics(current_user: User = Depends(get_current_active_user)):
    """Get system performance metrics."""
    try:
        metrics = await analytics_service.get_performance_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve performance metrics: {str(e)}"
        )

@router.get("/user")
async def get_user_analytics(
    days: int = 30,
    current_user: User = Depends(get_current_active_user)
):
    """Get detailed analytics for the current user."""
    try:
        analytics = await analytics_service.get_user_analytics(
            user_id=current_user.id,
            days=days
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user analytics: {str(e)}"
        )

@router.get("/system")
async def get_system_analytics(current_user: User = Depends(get_current_active_user)):
    """Get system-wide analytics (admin only)."""
    try:
        # In a real implementation, you'd check if user is admin
        analytics = await analytics_service.get_system_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve system analytics: {str(e)}"
        )

@router.get("/realtime")
async def get_real_time_metrics(current_user: User = Depends(get_current_active_user)):
    """Get real-time metrics for monitoring."""
    try:
        metrics = await analytics_service.get_real_time_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve real-time metrics: {str(e)}"
        )

@router.post("/events")
async def record_analytics_event(
    event_type: str,
    data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Record an analytics event."""
    try:
        success = await analytics_service.record_event(
            event_type=event_type,
            user_id=current_user.id,
            data=data
        )
        if success:
            return {"message": "Event recorded successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record event"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record analytics event: {str(e)}"
        )
