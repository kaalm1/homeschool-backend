from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import (
    ActivityType,
    AgeGroup,
    Cost,
    Duration,
    Location,
    Participants,
    Season,
    Theme,
)

from .base import BaseModel

if TYPE_CHECKING:
    from .kid import Kid
    from .user import User

# Define PostgreSQL ENUMs
cost_enum = ENUM(Cost, name="cost_enum", create_type=True)
duration_enum = ENUM(Duration, name="duration_enum", create_type=True)
participants_enum = ENUM(Participants, name="participants_enum", create_type=True)
location_enum = ENUM(Location, name="location_enum", create_type=True)
season_enum = ENUM(Season, name="season_enum", create_type=True)
age_group_enum = ENUM(AgeGroup, name="age_group_enum", create_type=True)
theme_enum = ENUM(Theme, name="theme_enum", create_type=True)
activity_type_enum = ENUM(ActivityType, name="activity_type_enum", create_type=True)


class Activity(BaseModel):
    """Activity model with enums, arrays, and relationships."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign key to User (family) - every activity belongs to a family
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Foreign key to Kid - NULL means family-level activity, value means kid-specific
    assigned_to_kid_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("kids.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activities")
    assigned_to_kid: Mapped[Optional["Kid"]] = relationship(
        "Kid", foreign_keys=[assigned_to_kid_id], back_populates="assigned_activities"
    )

    # ENUM arrays
    costs: Mapped[Optional[List[Cost]]] = mapped_column(ARRAY(cost_enum), nullable=True)
    durations: Mapped[Optional[List[Duration]]] = mapped_column(
        ARRAY(duration_enum), nullable=True
    )
    participants: Mapped[Optional[List[Participants]]] = mapped_column(
        ARRAY(participants_enum), nullable=True
    )
    locations: Mapped[Optional[List[Location]]] = mapped_column(
        ARRAY(location_enum), nullable=True
    )
    seasons: Mapped[Optional[List[Season]]] = mapped_column(
        ARRAY(season_enum), nullable=True
    )
    age_groups: Mapped[Optional[List[AgeGroup]]] = mapped_column(
        ARRAY(age_group_enum), nullable=True
    )
    themes: Mapped[Optional[List[AgeGroup]]] = mapped_column(
        ARRAY(theme_enum), nullable=True
    )
    types: Mapped[Optional[List[AgeGroup]]] = mapped_column(
        ARRAY(activity_type_enum), nullable=True
    )

    # Properties for easier checking
    @property
    def is_family_activity(self) -> bool:
        """True if this activity is assigned to the family (not a specific kid)."""
        return self.assigned_to_kid_id is None

    @property
    def is_kid_activity(self) -> bool:
        """True if this activity is assigned to a specific kid."""
        return self.assigned_to_kid_id is not None

    @property
    def assignee_name(self) -> str:
        """Returns the name of who the activity is assigned to."""
        if self.is_family_activity:
            return "Family"
        return self.assigned_to_kid.name if self.assigned_to_kid else "Unknown Kid"

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, title='{self.title}', kid_id={self.kid_id})>"
