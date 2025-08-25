from fastapi import APIRouter, Depends
from app.models import User
from app.core.security import get_current_active_user

router = APIRouter()

@router.get("/usage")
async def get_usage_analytics(current_user: User = Depends(get_current_active_user)):
    """Get usage analytics."""
    return {"usage": {"messages": 0, "conversations": 0}}

@router.get("/performance")
async def get_performance_metrics(current_user: User = Depends(get_current_active_user)):
    """Get performance metrics."""
    return {"performance": {"cpu": "45%", "memory":
