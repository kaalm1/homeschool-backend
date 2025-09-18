from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import (
    ActivityType,
    Cost,
    DaysOfWeek,
    GroupActivityComfort,
    Location,
    NewExperienceOpenness,
    PreferredTimeSlot,
    Theme,
)


class FamilyProfile(BaseModel):
    # Core Demographics
    family_size: int = Field(ge=1, le=20)
    adults_count: int = Field(ge=1, le=10)
    kids: List[Dict] = Field(default_factory=list)

    # Location & Mobility
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    max_travel_distance: int = Field(default=30)
    has_car: bool = Field(default=True)

    # Financial Constraints
    weekly_activity_budget: Optional[float] = None
    preferred_cost_ranges: List[str] = Field(default_factory=list)

    # Time Availability
    available_days: List[DaysOfWeek] = Field(default_factory=list)
    preferred_time_slots: List[PreferredTimeSlot] = Field(default_factory=list)
    max_activities_per_week: int = Field(default=5, ge=1, le=10)

    # Preferences
    preferred_themes: List[Theme] = Field(default_factory=list)
    preferred_activity_types: List[ActivityType] = Field(default_factory=list)
    group_activity_comfort: Optional[GroupActivityComfort] = Field(default=None)
    new_experience_openness: Optional[NewExperienceOpenness] = Field(default=None)


class FamilyPreferenceUpdateRequest(BaseModel):
    """Request model for updating family preferences."""

    preferred_themes: Optional[List[Theme]] = Field(
        None, description="Preferred activity themes"
    )
    preferred_activity_types: Optional[List[ActivityType]] = Field(
        None, description="Preferred activity types"
    )
    preferred_cost_ranges: Optional[List[Cost]] = Field(
        None, description="Preferred cost ranges"
    )
    preferred_locations: Optional[List[Location]] = Field(
        None, description="Preferred locations"
    )
    available_days: Optional[List[DaysOfWeek]] = Field(
        None, description="Available days of the week"
    )
    preferred_time_slots: Optional[List[PreferredTimeSlot]] = Field(
        None, description="Preferred time slots"
    )
    group_activity_comfort: Optional[GroupActivityComfort] = Field(
        None, description="Group activity comfort level"
    )
    new_experience_openness: Optional[NewExperienceOpenness] = Field(
        None, description="Openness to new experiences"
    )
    educational_priorities: Optional[List[str]] = Field(
        None, description="Educational priorities"
    )
    equipment_owned: Optional[List[str]] = Field(
        None, description="Equipment owned by family"
    )
    accessibility_needs: Optional[List[str]] = Field(
        None, description="Accessibility needs"
    )
    special_requirements: Optional[str] = Field(
        None, description="Special requirements"
    )

    class Config:
        use_enum_values = True


class FamilyPreferenceResponse(BaseModel):
    """Response model for family preferences."""

    id: Optional[int] = Field(None, description="Preference ID")
    user_id: Optional[int] = Field(None, description="User ID")
    preferred_themes: List[Theme] = Field(
        default_factory=list, description="Preferred activity themes"
    )
    preferred_activity_types: List[ActivityType] = Field(
        default_factory=list, description="Preferred activity types"
    )
    preferred_cost_ranges: List[Cost] = Field(
        default_factory=list, description="Preferred cost ranges"
    )
    preferred_locations: List[Location] = Field(
        default_factory=list, description="Preferred locations"
    )
    available_days: List[DaysOfWeek] = Field(
        default_factory=list, description="Available days of the week"
    )
    preferred_time_slots: List[PreferredTimeSlot] = Field(
        default_factory=list, description="Preferred time slots"
    )
    group_activity_comfort: Optional[GroupActivityComfort] = Field(
        default=None, description="Group activity comfort level"
    )
    new_experience_openness: Optional[NewExperienceOpenness] = Field(
        default=None, description="Openness to new experiences"
    )
    educational_priorities: List[str] = Field(
        default_factory=list, description="Educational priorities"
    )
    equipment_owned: List[str] = Field(
        default_factory=list, description="Equipment owned by family"
    )
    accessibility_needs: List[str] = Field(
        default_factory=list, description="Accessibility needs"
    )
    special_requirements: Optional[str] = Field(
        default=None, description="Special requirements"
    )
    updated_at: Optional[datetime] = Field(
        default=None, description="Last update timestamp"
    )

    class Config:
        from_attributes = True
