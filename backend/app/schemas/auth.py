"""
Authentication schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


class TokenData(BaseModel):
    """Token data schema"""
    username: Optional[str] = Field(None, description="Username from token")
    user_id: Optional[int] = Field(None, description="User ID from token")
    is_superuser: Optional[bool] = Field(None, description="Is superuser")
    roles: list[str] = Field(default_factory=list, description="User roles")
