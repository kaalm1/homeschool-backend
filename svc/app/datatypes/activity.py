from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.common import TimestampMixin
from svc.app.datatypes.enums import (
    ActivityType,
    AgeGroup,
    Cost,
    Duration,
    Frequency,
    Location,
    Participants,
    Season,
    Theme,
)


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
    frequency: Optional[Frequency] = Field(None, description="Activity frequency")
    themes: Optional[Theme] = Field(None, description="Activity theme")
    types: Optional[ActivityType] = Field(None, description="Activity type")


class ActivityCreate(ActivityBase):
    kid_id: Optional[int] = Field(None, description="Kid ID")


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
    frequency: Optional[Frequency] = Field(None, description="Activity frequency")
    themes: Optional[List[Theme]] = Field(None, description="Theme IDs")
    types: Optional[List[ActivityType]] = Field(None, description="ActivityType IDs")


class ActivityResponse(ActivityBase, TimestampMixin):
    id: int = Field(..., description="Activity ID")
    done: bool = Field(..., description="Activity completion status")
    kid_id: Optional[int] = Field(None, description="Kid ID")

    class Config:
        from_attributes = True


class ActivityToggleRequest(BaseModel):
    id: int = Field(..., description="Activity ID")


class RewardSummary(BaseModel):
    kid_id: int = Field(..., description="Kid ID")
    kid_name: str = Field(..., description="Kid name")
    stars: int = Field(..., ge=0, description="Number of stars earned")
