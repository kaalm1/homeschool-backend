from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

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
    address: Optional[str] = Field(None, description="User location address")
    family_size: Optional[int] = Field(None, description="User family size")
    latitude: Optional[float] = Field(None, description="User latitude")
    longitude: Optional[float] = Field(None, description="User longitude")
    zipcode: Optional[str] = Field(None, description="User zipcode")
    city: Optional[str] = Field(None, description="User city")
    state: Optional[str] = Field(None, description="User state")
    max_activities_per_week: Optional[int] = Field()
    has_car: bool = Field(..., description="User has car")


class UserResponse(UserBase, TimestampMixin):
    """User response model."""

    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="User active status")
    address: Optional[str] = Field(None, description="User location address")
    zipcode: Optional[str] = Field(None, description="User zipcode")
    family_size: Optional[int] = Field(None, description="User family size")
    max_activities_per_week: Optional[int] = Field()
    has_car: bool = Field(..., description="User has car")

    class Config:
        from_attributes = True


class UserWithKidsResponse(UserResponse):
    """User response with kids included."""

    kids: List[KidResponse] = Field(default_factory=list, description="User's kids")
