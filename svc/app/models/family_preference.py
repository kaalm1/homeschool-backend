from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class FamilyPreferences(BaseModel):
    """Complex family preferences that change frequently."""

    __tablename__ = "family_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Activity Type Preferences (arrays for flexibility)
    preferred_themes: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    preferred_activity_types: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    preferred_cost_ranges: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )
    preferred_locations: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )

    # Time Preferences (changes seasonally/situationally)
    available_days: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # ["saturday", "sunday"]
    preferred_time_slots: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True
    )  # ["morning", "afternoon"]

    # Social & Learning Preferences
    group_activity_comfort: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # low/medium/high
    new_experience_openness: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # conservative/medium/adventurous
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
