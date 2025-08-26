from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .common import TimestampMixin


class ActivityBase(BaseModel):
    """Base activity model."""

    title: str = Field(..., min_length=1, max_length=200, description="Activity title")
    subject: str = Field(
        default="General", max_length=100, description="Activity subject"
    )


class ActivityCreate(ActivityBase):
    """Activity creation model."""

    kid_id: int = Field(..., description="Kid ID")


class ActivityUpdate(BaseModel):
    """Activity update model."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Activity title"
    )
    subject: Optional[str] = Field(None, max_length=100, description="Activity subject")
    done: Optional[bool] = Field(None, description="Activity completion status")


class ActivityResponse(ActivityBase, TimestampMixin):
    """Activity response model."""

    id: int = Field(..., description="Activity ID")
    done: bool = Field(..., description="Activity completion status")
    kid_id: int = Field(..., description="Kid ID")

    class Config:
        from_attributes = True


class ActivityToggleRequest(BaseModel):
    """Activity toggle request model."""

    id: int = Field(..., description="Activity ID")


class RewardSummary(BaseModel):
    """Reward summary model."""

    kid_id: int = Field(..., description="Kid ID")
    kid_name: str = Field(..., description="Kid name")
    stars: int = Field(..., ge=0, description="Number of stars earned")
