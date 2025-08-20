from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import User
from app.schemas.user import UserCreate, UserUpdate, UserInDB, UserPublic
from app.core.security import get_current_active_user, get_password_hash, verify_password
from app.core.security_metrics import security_metrics
from app.services.email import email_service
from datetime import datetime, timedelta
import secrets

router = APIRouter()

@router.get("/", response_model=List[UserPublic])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search users by username or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve all users with optional filtering and search."""
    query = db.query(User)

    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserPublic)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create new user."""
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )

    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Send welcome email
    await email_service.send_welcome_email(db_user.email, db_user.username)

    security_metrics.record_security_event("user_created", "info", {
        "user_id": db_user.id,
        "email": db_user.email
    })

    return db_user

@router.get("/me", response_model=UserPublic)
async def read_user_me(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user."""
    return current_user

@router.put("/me", response_model=UserPublic)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update current user."""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    security_metrics.record_security_event("user_updated", "info", {
        "user_id": current_user.id,
        "updated_fields": list(user_update.dict(exclude_unset=True).keys())
    })

    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete current user account."""
    user_id = current_user.id
    db.delete(current_user)
    db.commit()

    security_metrics.record_security_event("user_deleted_self", "warning", {
        "user_id": user_id
    })

    return None

@router.get("/{user_id}", response_model=UserPublic)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserPublic)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    security_metrics.record_security_event("user_updated_by_admin", "info", {
        "user_id": user_id,
        "admin_id": current_user.id,
        "updated_fields": list(user_update.dict(exclude_unset=True).keys())
    })

    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    security_metrics.record_security_event("user_deleted_by_admin", "warning", {
        "user_id": user_id,
        "admin_id": current_user.id
    })

    return None

@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Reset user password and send reset email."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_token_expiry = datetime.utcnow() + timedelta(hours=24)

    user.password_reset_token = reset_token
    user.password_reset_token_expires = reset_token_expiry
    db.commit()

    # Send password reset email
    await email_service.send_password_reset_email(user.email, reset_token)

    security_metrics.record_security_event("password_reset_requested", "info", {
        "user_id": user_id,
        "admin_id": current_user.id
    })

    return {"message": "Password reset email sent"}

@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Activate user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    security_metrics.record_security_event("user_activated", "info", {
        "user_id": user_id,
        "admin_id": current_user.id
    })

    return {"message": "User activated successfully"}

@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Deactivate user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot deactivate your own account"
        )

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    security_metrics.record_security_event("user_deactivated", "warning", {
        "user_id": user_id,
        "admin_id": current_user.id
    })

