from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import RepetitionTolerance


class FamilyProfile(BaseModel):
    # Core Demographics
    family_size: int = Field(ge=1, le=20)
    adults_count: int = Field(ge=1, le=10)
    kids: List[Dict] = Field(default=[])

    # Location & Mobility
    home_location: str
    home_coordinates: Optional[tuple[float, float]] = None
    max_travel_distance: int = Field(default=30)
    has_car: bool = Field(default=True)

    # Financial Constraints
    weekly_activity_budget: Optional[float] = None
    preferred_cost_ranges: List[str] = Field(default=["FREE", "LOW"])

    # Time Availability
    available_days: List[str] = Field(default=["saturday", "sunday"])
    preferred_time_slots: List[str] = Field(default=["morning", "afternoon"])
    max_activities_per_week: int = Field(default=5, ge=1, le=10)

    # Preferences
    preferred_themes: List[str] = Field(default=[])
    preferred_activity_types: List[str] = Field(default=[])
    group_activity_comfort: str = Field(default="medium")
    new_experience_openness: str = Field(default="medium")
