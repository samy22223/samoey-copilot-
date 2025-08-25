from fastapi import APIRouter, Depends
from app.models import User
from app.core.security import get_current_active_user

router = APIRouter()

@router.get("/")
async def get_notifications(current_user: User = Depends(get_current_active_user)):
    """Get user notifications."""
    return {"notifications": []}
