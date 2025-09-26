"""
User schemas
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    is_active: bool = Field(True, description="Is user active")


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=6, description="Password")


class UserUpdate(BaseModel):
    """User update schema"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserLogin(BaseModel):
    """User login schema"""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class User(UserBase):
    """User response schema"""
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    roles: List[str] = Field(default_factory=list, description="User roles")
    
    class Config:
        from_attributes = True
