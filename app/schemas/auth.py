from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: str

class TokenData(BaseModel):
    """Token payload schema"""
    username: Optional[str] = None

class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)

class UserRegister(BaseModel):
    """User registration schema"""
    username: str = Field(..., min_length=3, max_length=50, regex="^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=100)

class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

class ChangePassword(BaseModel):
    """Change password schema"""
    current_password: str = Field(..., min_length=8, max_length=100)
    new_password: str = Field(..., min_length=8, max_length=100)
