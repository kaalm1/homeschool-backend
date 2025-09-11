from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class UserBehaviorAnalytic(BaseModel):
    """Analytics and behavioral patterns - updated automatically."""

    __tablename__ = "user_behavior_analytics"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )

    # Marking Behavior Patterns
    marking_rate: Mapped[float] = mapped_column(Float, default=0.1, nullable=False)
    marks_big_activities_only: Mapped[bool] = mapped_column(
        default=True, nullable=False
    )
    big_activity_marking_rate: Mapped[float] = mapped_column(
        Float, default=0.3, nullable=False
    )
    small_activity_marking_rate: Mapped[float] = mapped_column(
        Float, default=0.05, nullable=False
    )

    # Activity Success Patterns (JSON for flexibility)
    successful_themes: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"OUTDOOR": 0.8, "CREATIVE": 0.6}
    successful_activity_types: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )
    successful_cost_ranges: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    successful_durations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Environmental Factors
    weather_sensitivity: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )
    seasonal_patterns: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # System Metadata
    last_calculated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    calculation_confidence: Mapped[float] = mapped_column(
        Float, default=0.5, nullable=False
    )  # How confident we are in patterns
    sample_size: Mapped[int] = mapped_column(
        default=0, nullable=False
    )  # Number of activities analyzed

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="behavior_analytics")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "marking_rate": self.marking_rate,
            "marks_big_only": self.marks_big_activities_only,
            "big_activity_marking_rate": self.big_activity_marking_rate,
            "small_activity_marking_rate": self.small_activity_marking_rate,
            "successful_themes": self.successful_themes or {},
            "successful_activity_types": self.successful_activity_types or {},
            "weather_sensitivity": self.weather_sensitivity,
            "confidence": self.calculation_confidence,
        }
