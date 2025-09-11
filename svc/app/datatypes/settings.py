from typing import List

from pydantic import BaseModel


class EnumOption(BaseModel):
    """Standard structure for enum options."""

    value: str
    label: str


class PreferenceOptionsResponse(BaseModel):
    """Response model for preference options."""

    learning_priorities: List[EnumOption]
    preferred_time_slots: List[EnumOption]
    group_activity_comfort: List[EnumOption]
    new_experience_openness: List[EnumOption]
    available_days: List[EnumOption]


class FilterOptionsResponse(BaseModel):
    """Response model for filter options."""

    costs: List[EnumOption]
    durations: List[EnumOption]
    participants: List[EnumOption]
    locations: List[EnumOption]
    seasons: List[EnumOption]
    age_groups: List[EnumOption]
    frequency: List[EnumOption]
    themes: List[EnumOption]
    activity_types: List[EnumOption]


class AllSettingsResponse(BaseModel):
    """Response model for all settings options."""

    filters: FilterOptionsResponse
    preferences: PreferenceOptionsResponse
