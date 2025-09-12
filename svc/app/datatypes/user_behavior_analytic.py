from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import RepetitionTolerance


# Pydantic Schemas
class WeatherDay(BaseModel):
    date: date
    condition: str
    temperature_range: tuple[int, int]
    precipitation_chance: int
    suitable_for_outdoor: bool


class WeeklyContext(BaseModel):
    target_week_start: date
    weather_forecast: List[WeatherDay]
    season: str
    local_events: Optional[List[str]] = None
    school_schedule: Optional[str] = None


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
    encourage_repetition: List[ActivityRepetitionInfo] = Field(max_items=10)
    moderate_cooldown: List[ActivityCooldownInfo] = Field(max_items=15)
    avoid_repetition: List[ActivityCooldownInfo] = Field(max_items=20)
    successful_patterns: Dict[str, Any] = Field(default={})
    avoided_patterns: Dict[str, Any] = Field(default={})
    favorite_themes: List[tuple[str, int]] = Field(max_items=5)
    preferred_durations: List[str] = Field(max_items=3)
