from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.user import UserInResponse, UsersInResponse, UserUpdate
from backend.core.security import get_current_active_user, get_current_active_superuser

router = APIRouter()

@router.get("/me", response_model=UserInResponse)
async def read_user_me(current_user: User = Depends(get_current_active_user)):
    return {"user": current_user}

@router.get("/", response_model=UsersInResponse)
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return {"users": users, "count": db.query(User).count()}

@router.put("/me", response_model=UserInResponse)
async def update_user_me(
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return {"user": current_user}
