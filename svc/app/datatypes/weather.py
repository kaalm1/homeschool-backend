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
        Derive precipitation_chance, suitability, and advisories from inputs.
        Heuristics:
         - Map precip mm bands to chance %
         - Mark thunderstorms, heavy rain, heavy snow as advisories
         - Mark as unsuitable if thunderstorm / high precip chance / extreme temps / heavy snow
        """

        # keep this helper local to validator
        def estimate_precip_chance(mm: float, rain_mm: float, snow_mm: float) -> int:
            if mm <= 0.0:
                return 5
            if mm < 1.0:
                return 20
            if mm < 5.0:
                return 50
            if mm < 15.0:
                return 80
            return 95

        d_low, d_high = values.get("temperature_range", (None, None))
        precip = float(values.get("precipitation_mm", 0.0) or 0.0)
        rain = float(values.get("rain_mm", 0.0) or 0.0)
        snow = float(values.get("snow_mm", 0.0) or 0.0)
        condition = values.get("condition", "")

        # precipitation chance heuristic
        precip_pct = estimate_precip_chance(precip, rain, snow)
        values["precipitation_chance"] = precip_pct

        reasons: List[str] = []
        advisories: List[str] = []

        # condition-based advisories
        if "Thunderstorm" in condition or "thunder" in condition.lower():
            advisories.append("Thunderstorms expected")
        if precip >= 15.0:
            advisories.append("Heavy precipitation expected")
        if snow >= 5.0:
            advisories.append("Significant snowfall expected")
        if d_high is not None and d_high >= 32:  # 32°C threshold for heat stress
            advisories.append("High temperatures (heat risk)")
        if d_low is not None and d_low <= -5:  # cold advisory
            advisories.append("Very cold overnight temperatures")

        # suitability heuristics: combine multiple signals
        suitable = True

        # immediate disqualifiers
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

        # temperature-based considerations
        if d_high is not None and d_low is not None:
            # comfortable high-range: 10-28°C (modify for your users)
            if d_high < 5:
                suitable = False
                reasons.append(f"Too cold during the day (high {d_high}°C)")
            if d_high >= 30:
                # still may be possible but risky (heat); mark as less suitable
                reasons.append(f"Warm to hot during the day (high {d_high}°C)")
            # big diurnal swings
            if (d_high - d_low) >= 15:
                reasons.append(f"Large temp swing ({d_low}°C → {d_high}°C)")

        # minor rain but still possible (e.g., sprinkling) - may still be suitable for some activities
        if 20 <= precip_pct < 80 and not reasons:
            reasons.append(f"Light-to-moderate precipitation chance ({precip_pct}%)")

        # if no reasons and no advisories, mark positive reasons
        if not reasons:
            reasons.append("Temperatures and precipitation favorable")

        values["suitability_reasons"] = reasons
        values["advisories"] = advisories
        values["suitable_for_outdoor"] = suitable
        return values
