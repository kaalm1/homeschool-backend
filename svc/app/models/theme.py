from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity


# ---------------------------
# Theme
# ---------------------------
class Theme(BaseModel):
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Reverse many-to-many relationship
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", secondary="activity_themes", back_populates="themes"
    )


# ---------------------------
# Junction table: Activity <-> Theme
# ---------------------------
class ActivityTheme(BaseModel):
    __tablename__ = "activity_themes"

    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id"), primary_key=True
    )
    theme_id: Mapped[int] = mapped_column(ForeignKey("themes.id"), primary_key=True)
