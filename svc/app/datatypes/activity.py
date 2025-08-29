from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import TimestampMixin
from .enums import AgeGroup, Cost, Duration, Location, Participants, Season


# ---------------------------
# Nested models for relations
# ---------------------------
class ThemeResponse(BaseModel):
    id: int = Field(..., description="Theme ID")
    name: str = Field(..., description="Theme name")

    class Config:
        from_attributes = True


class ActivityTypeResponse(BaseModel):
    id: int = Field(..., description="ActivityType ID")
    name: str = Field(..., description="Activity type name")

    class Config:
        from_attributes = True


# ---------------------------
# Base models
# ---------------------------
class ActivityBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Activity title")
    description: Optional[str] = Field(None, description="Activity description")

    # Enum arrays
    costs: Optional[List[Cost]] = Field(None, description="Activity costs")
    durations: Optional[List[Duration]] = Field(None, description="Activity durations")
    participants: Optional[List[Participants]] = Field(
        None, description="Activity participants"
    )
    locations: Optional[List[Location]] = Field(None, description="Activity locations")
    seasons: Optional[List[Season]] = Field(None, description="Activity seasons")
    age_groups: Optional[List[AgeGroup]] = Field(
        None, description="Activity age groups"
    )


class ActivityCreate(ActivityBase):
    kid_id: int = Field(..., description="Kid ID")


class ActivityUpdate(BaseModel):
    title: Optional[str] = Field(
        None, min_length=1, max_length=200, description="Activity title"
    )
    description: Optional[str] = Field(None, description="Activity description")
    done: Optional[bool] = Field(None, description="Activity completion status")

    costs: Optional[List[Cost]] = Field(None, description="Activity costs")
    durations: Optional[List[Duration]] = Field(None, description="Activity durations")
    participants: Optional[List[Participants]] = Field(
        None, description="Activity participants"
    )
    locations: Optional[List[Location]] = Field(None, description="Activity locations")
    seasons: Optional[List[Season]] = Field(None, description="Activity seasons")
    age_groups: Optional[List[AgeGroup]] = Field(
        None, description="Activity age groups"
    )

    themes: Optional[List[int]] = Field(None, description="Theme IDs")
    types: Optional[List[int]] = Field(None, description="ActivityType IDs")


class ActivityResponse(ActivityBase, TimestampMixin):
    id: int = Field(..., description="Activity ID")
    done: bool = Field(..., description="Activity completion status")
    kid_id: int = Field(..., description="Kid ID")

    # Nested responses
    themes: Optional[List[ThemeResponse]] = Field(None, description="Activity themes")
    types: Optional[List[ActivityTypeResponse]] = Field(
        None, description="Activity types"
    )

    class Config:
        from_attributes = True


class ActivityToggleRequest(BaseModel):
    id: int = Field(..., description="Activity ID")


class RewardSummary(BaseModel):
    kid_id: int = Field(..., description="Kid ID")
    kid_name: str = Field(..., description="Kid name")
    stars: int = Field(..., ge=0, description="Number of stars earned")
