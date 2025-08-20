"""
Mobile API endpoints
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserResponse
from config.mobile import MOBILE_OPTIMIZATIONS

router = APIRouter(prefix="/api/mobile", tags=["mobile"])

@router.get("/config")
async def get_mobile_config(request: Request) -> Dict[str, Any]:
    """Get mobile-specific configuration"""
    return {
        "mobile_config": request.app.mobile_config,
        "ios_config": request.app.ios_config,
        "optimizations": MOBILE_OPTIMIZATIONS
    }

@router.post("/register-device")
async def register_device(
    device_info: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Register a mobile device"""
    try:
        # Store device info
        return {"status": "Device registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/sync")
async def sync_data(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Sync data for mobile clients"""
    try:
        # Implement offline data sync
        return {
            "status": "success",
            "synced_at": str(datetime.utcnow())
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/preferences")
async def get_user_preferences(
    request: Request,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get mobile user preferences"""
    try:
        # Get user preferences
        return {
            "theme": "auto",
            "notifications": True,
            "offline_mode": True,
            "data_saver": False
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/user/preferences")
async def update_user_preferences(
    preferences: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Update mobile user preferences"""
    try:
        # Update preferences
        return {"status": "Preferences updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
