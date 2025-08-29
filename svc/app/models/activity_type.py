from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity


# ---------------------------
# ActivityType
# ---------------------------
class ActivityType(BaseModel):
    __tablename__ = "activity_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String, unique=True, nullable=False
    )  # e.g., "Board Game"
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Reverse many-to-many relationship
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", secondary="activity_activity_types", back_populates="types"
    )


# ---------------------------
# Junction table: Activity <-> ActivityType
# ---------------------------
class ActivityActivityType(BaseModel):
    __tablename__ = "activity_activity_types"

    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), primary_key=True
    )
    type_id: Mapped[int] = mapped_column(
        ForeignKey("activity_types.id"), primary_key=True
    )
