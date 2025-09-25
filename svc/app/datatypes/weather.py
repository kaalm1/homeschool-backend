from datetime import date
from typing import List, Optional, Tuple

from pydantic import BaseModel, model_validator


class WeatherInputs(BaseModel):
    location: Optional[str] = None
    zipcode: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    target_week: date = date.today()
    is_valid_input: bool = True  # default, will be updated

    @model_validator(mode="after")
    def validate_location_or_coordinates(self) -> "WeatherInputs":
        if self.location or (self.lat is not None and self.lon is not None):
            self.is_valid_input = True
        else:
            self.is_valid_input = False
        return self


class WeatherDay(BaseModel):
    """
    One day's weather including raw fields and derived fields LLMs will need.
    temperature_range: (low_c, high_c)
    precipitation_mm: total precipitation for day (mm)
    rain_mm, snow_mm: components if available
    precipitation_chance: derived % (0-100)
    suitable_for_outdoor: boolean decision based on heuristics
    suitability_reasons: why it's (not) suitable
    advisories: short flags like 'Heavy rain', 'Thunderstorms', 'Snow accumulation'
    """

    date: date
    condition: str
    temperature_range: Tuple[float, float]
    precipitation_mm: float = 0.0
    rain_mm: float = 0.0
    snow_mm: float = 0.0

    # Derived fields (computed automatically)
    precipitation_chance: int = 0
    suitable_for_outdoor: bool = True
    suitability_reasons: List[str] = []
    advisories: List[str] = []

    @model_validator(mode="after")
    def compute_derived(cls, values) -> "WeatherDay":
        """
        Compute derived fields after model creation.
        """

        # helper to estimate precipitation chance
        def estimate_precip_chance(mm: float) -> int:
            if mm <= 0.0:
                return 5
            if mm < 1.0:
                return 20
            if mm < 5.0:
                return 50
            if mm < 15.0:
                return 80
            return 95

        # safely access fields
        low, high = values.temperature_range
        precip = float(values.precipitation_mm or 0.0)
        rain = float(values.rain_mm or 0.0)
        snow = float(values.snow_mm or 0.0)
        condition = values.condition

        # compute precipitation chance
        precip_pct = estimate_precip_chance(precip)
        values.precipitation_chance = precip_pct

        # initialize advisories & reasons
        advisories: List[str] = []
        reasons: List[str] = []

        # condition-based advisories
        if "Thunderstorm" in condition or "thunder" in condition.lower():
            advisories.append("Thunderstorms expected")
        if precip >= 15.0:
            advisories.append("Heavy precipitation expected")
        if snow >= 5.0:
            advisories.append("Significant snowfall expected")
        if high >= 32:
            advisories.append("High temperatures (heat risk)")
        if low <= -5:
            advisories.append("Very cold overnight temperatures")

        # suitability heuristics
        suitable = True
        if (
            any("Thunderstorm" in a for a in advisories)
            or precip_pct >= 80
            or snow >= 5.0
        ):
            suitable = False
            if precip_pct >= 80:
                reasons.append(f"High chance of precipitation ({precip_pct}%)")
            if snow >= 5.0:
                reasons.append("Snow accumulation likely")
            if any("Thunderstorms" in a for a in advisories):
                reasons.append("Thunderstorm risk")

        # temperature considerations
        if high < 5:
            suitable = False
            reasons.append(f"Too cold during the day (high {high}°C)")
        if high >= 30:
            reasons.append(f"Warm to hot during the day (high {high}°C)")
        if (high - low) >= 15:
            reasons.append(f"Large temp swing ({low}°C → {high}°C)")

        # minor precipitation but still suitable
        if 20 <= precip_pct < 80 and not reasons:
            reasons.append(f"Light-to-moderate precipitation chance ({precip_pct}%)")

        if not reasons:
            reasons.append("Temperatures and precipitation favorable")

        # assign back to model
        values.suitability_reasons = reasons
        values.advisories = advisories
        values.suitable_for_outdoor = suitable

        return values
