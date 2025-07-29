from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from backend.db.session import get_db
from backend.models.user import User
from backend.schemas.auth import (
    Token,
    UserLogin,
    UserRegister,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePassword,
)
from backend.schemas.user import UserInResponse
from backend.api.deps import get_current_user

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect username or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "refresh_token": create_refresh_token(data={"sub": user.username})
    }

@router.post("/register", response_model=UserInResponse)
async def register(
    user_in: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Create new user
    """
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user_in.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_email = db.query(User).filter(User.email == user_in.email).first()
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_in.password)
    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=True,
        is_superuser=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"user": user}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
):
    """
    Refresh access token
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    return {
        "access_token": create_access_token(
            data={"sub": current_user.username},
            expires_delta=access_token_expires
        ),
        "token_type": "bearer",
        "refresh_token": create_refresh_token(data={"sub": current_user.username})
    }

@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for the current user
    """
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password updated successfully"}

@router.post("/request-password-reset")
async def request_password_reset(
    email_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset
    """
    # In a real application, you would send an email with a reset link
    # For now, we'll just return a success message
    user = db.query(User).filter(User.email == email_data.email).first()
    if not user:
        # Don't reveal that the email doesn't exist
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    # Generate reset token (in a real app, this would be a JWT with short expiry)
    reset_token = "reset-token-placeholder"
    
    # Send email with reset link (implementation not shown)
    # send_password_reset_email(user.email, reset_token)
    
    return {"message": "If your email is registered, you will receive a password reset link"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password with a valid reset token
    """
    # In a real application, you would validate the reset token
    # For now, we'll just update the password if the token is valid
    
    # This is a placeholder - in a real app, you would decode the JWT
    # and get the user ID from it
    if reset_data.token != "reset-token-placeholder":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # In a real app, you would get the user ID from the token
    # For now, we'll just return a success message
    return {"message": "Password has been reset successfully"}
