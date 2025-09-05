import json
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import ActivityType, Theme, Cost, Location


# TODO: Update this
class ActivityPlannerRequest(BaseModel):
    data: str
    current_date: Optional[date] = Field(
        default=None, description="Date for the week (defaults to current date)"
    )


class PlannedActivity(BaseModel):
    id: int
    title: Optional[str] = None
    why_it_fits: Optional[str] = None

    @classmethod
    def from_llm(cls, content: str) -> List["PlannedActivity"]:
        """Parse a JSON string into a list of PlannedActivity objects."""
        raw_data = json.loads(content)  # list of dicts
        return [cls(**item) for item in raw_data]

    @classmethod
    def from_json(cls, content: list) -> List["PlannedActivity"]:
        """Parse a JSON string into a list of TaggedActivity objects."""
        return [cls(**item) for item in content]


class PlannedActivityFamilyInfo(BaseModel):
    family_size: int
    kids_ages: List[int]
    home_location: str
    home_latitude: float
    home_longitude: float
    theme_preference: List[Theme]
    activity_type_preference: List[ActivityType]
    budget_limit: List[Cost]
    location: List[Location]
    hours_unavailable: int


class PlannedActivityContextInfo(BaseModel):
    weather: List[dict]
    additional_notes: Optional[str]


class PlannedActivityLlmData(BaseModel):
    family: dict
    context: dict
    activities: List[dict]
