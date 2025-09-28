from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import RepetitionTolerance
from svc.app.datatypes.weather import WeatherDay


class WeeklyContext(BaseModel):
    target_week_start: date
    weather_forecast: List[WeatherDay]
    season: str
    local_events: Optional[List[str]] = None
    school_schedule: Optional[str] = None
    additional_notes: Optional[str] = None
    max_activities: Optional[int] = None


class ActivityRepetitionInfo(BaseModel):
    activity_id: int
    activity_title: str
    completion_rate: float
    frequency: int
    last_suggested: Optional[date] = None
    recommendation: str
    tolerance_level: RepetitionTolerance


class ActivityCooldownInfo(BaseModel):
    activity_id: int
    activity_title: str
    weeks_until_available: int
    reason: str
    tolerance_level: RepetitionTolerance


class PastActivityContext(BaseModel):
    encourage_repetition: List[ActivityRepetitionInfo] = Field(
        default_factory=list, max_length=10
    )
    moderate_cooldown: List[ActivityCooldownInfo] = Field(
        default_factory=list, max_length=15
    )
    avoid_repetition: List[ActivityCooldownInfo] = Field(
        default_factory=list, max_length=20
    )
    successful_patterns: Dict[str, Any] = Field(default_factory=dict)
    avoided_patterns: Dict[str, Any] = Field(default_factory=dict)
    favorite_themes: List[tuple[str, int]] = Field(default_factory=list, max_length=5)
    preferred_durations: List[str] = Field(default_factory=list, max_length=3)
