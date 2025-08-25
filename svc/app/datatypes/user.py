from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

from .common import TimestampMixin
from .kid import KidResponse


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(..., min_length=6, description="User password")


class UserUpdate(BaseModel):
    """User update model."""

    email: Optional[EmailStr] = Field(None, description="User email address")
    is_active: Optional[bool] = Field(None, description="User active status")


class UserResponse(UserBase, TimestampMixin):
    """User response model."""

    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="User active status")

    class Config:
        from_attributes = True


class UserWithKidsResponse(UserResponse):
    """User response with kids included."""

    kids: List[KidResponse] = Field(default=[], description="User's kids")
