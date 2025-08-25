from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from .common import TimestampMixin


class KidBase(BaseModel):
    """Base kid model."""

    name: str = Field(..., min_length=1, max_length=100, description="Kid's name")
    color: str = Field(
        default="#a7f3d0", pattern=r"^#[0-9A-Fa-f]{6}$", description="Kid's color (hex)"
    )


class KidCreate(KidBase):
    """Kid creation model."""

    pass


class KidUpdate(BaseModel):
    """Kid update model."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Kid's name"
    )
    color: Optional[str] = Field(
        None, pattern=r"^#[0-9A-Fa-f]{6}$", description="Kid's color (hex)"
    )


class KidResponse(KidBase, TimestampMixin):
    """Kid response model."""

    id: int = Field(..., description="Kid ID")
    parent_id: int = Field(..., description="Parent user ID")

    class Config:
        from_attributes = True


class KidWithActivitiesResponse(KidResponse):
    """Kid response with activities included."""

    activities: List["ActivityResponse"] = Field(
        default=[], description="Kid's activities"
    )


# Forward reference resolution
from .activity import ActivityResponse

KidWithActivitiesResponse.model_rebuild()
