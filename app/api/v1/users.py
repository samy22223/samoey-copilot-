from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.core.security import get_current_active_user

router = APIRouter()

@router.get("/")
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all users."""
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.get("/me")
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    """Get current user."""
    return current_user
