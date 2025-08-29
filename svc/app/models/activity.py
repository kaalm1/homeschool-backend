from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import (AgeGroup, Cost, Duration, Location,
                                     Participants, Season)

from .base import BaseModel

if TYPE_CHECKING:
    from .activity_type import ActivityType
    from .kid import Kid
    from .theme import Theme

# Define PostgreSQL ENUMs
cost_enum = ENUM(Cost, name="cost_enum", create_type=True)
duration_enum = ENUM(Duration, name="duration_enum", create_type=True)
participants_enum = ENUM(Participants, name="participants_enum", create_type=True)
location_enum = ENUM(Location, name="location_enum", create_type=True)
season_enum = ENUM(Season, name="season_enum", create_type=True)
age_group_enum = ENUM(AgeGroup, name="age_group_enum", create_type=True)


class Activity(BaseModel):
    """Activity model with enums, arrays, and relationships."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Foreign key to Kid
    kid_id: Mapped[int] = mapped_column(
        ForeignKey("kids.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kid: Mapped["Kid"] = relationship("Kid", back_populates="activities")

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

    # Many-to-many relationships
    themes: Mapped[List["Theme"]] = relationship(
        "Theme", secondary="activity_themes", back_populates="activities"
    )
    types: Mapped[List["ActivityType"]] = relationship(
        "ActivityType",
        secondary="activity_activity_types",  # ← this is the actual junction table
        back_populates="activities",
    )

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, title='{self.title}', kid_id={self.kid_id})>"
