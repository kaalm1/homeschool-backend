from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import (ActivityScale, ActivityType, AgeGroup,
                                     Cost, DaysOfWeek, Duration, Frequency,
                                     GroupActivityComfort, Location,
                                     NewExperienceOpenness, Participants,
                                     PreferredTimeSlot, Season, Theme)

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


cost_enum = ENUM(Cost, name="cost_enum", create_type=True)
location_enum = ENUM(Location, name="location_enum", create_type=True)
theme_enum = ENUM(Theme, name="theme_enum", create_type=True)
activity_type_enum = ENUM(ActivityType, name="activity_type_enum", create_type=True)
days_of_week_enum = ENUM(DaysOfWeek, name="days_of_week", create_type=True)
preferred_time_slot_enum = ENUM(
    PreferredTimeSlot, name="preferred_time_slot", create_type=True
)
group_activity_comfort_enum = ENUM(
    GroupActivityComfort, name="group_activity_comfort", create_type=True
)
new_experience_openness_enum = ENUM(
    NewExperienceOpenness, name="new_experience_openness", create_type=True
)


class FamilyPreferences(BaseModel):
    """Complex family preferences that change frequently."""

    __tablename__ = "family_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Activity Type Preferences (arrays for flexibility)
    preferred_themes: Mapped[Optional[List[Theme]]] = mapped_column(
        ARRAY(theme_enum), nullable=True
    )
    preferred_activity_types: Mapped[Optional[List[ActivityType]]] = mapped_column(
        ARRAY(activity_type_enum), nullable=True
    )
    preferred_cost_ranges: Mapped[Optional[List[Cost]]] = mapped_column(
        ARRAY(cost_enum), nullable=True
    )
    preferred_locations: Mapped[Optional[List[Location]]] = mapped_column(
        ARRAY(location_enum), nullable=True
    )

    # Time Preferences (changes seasonally/situationally)
    available_days: Mapped[Optional[List[DaysOfWeek]]] = mapped_column(
        ARRAY(days_of_week_enum), nullable=True
    )
    preferred_time_slots: Mapped[Optional[List[PreferredTimeSlot]]] = mapped_column(
        ARRAY(preferred_time_slot_enum), nullable=True
    )

    # Social & Learning Preferences
    group_activity_comfort: Mapped[Optional[GroupActivityComfort]] = mapped_column(
        String(20), nullable=True
    )
    new_experience_openness: Mapped[Optional[NewExperienceOpenness]] = mapped_column(
        String(20), nullable=True
    )
    educational_priorities: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # ["stem", "arts", "social"]

    # Practical Constraints
    equipment_owned: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # ["bikes", "sports_equipment"]
    accessibility_needs: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    special_requirements: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Free-form text for complex needs

    # Metadata
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="family_preferences")
