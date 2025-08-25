from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class RegisterRequest(BaseModel):
    """Registration request model."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class TokenData(BaseModel):
    """Token data model."""

    email: Optional[str] = None
    user_id: Optional[int] = None
