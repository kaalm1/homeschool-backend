from typing import TYPE_CHECKING, List
from datetime import date

from sqlalchemy import ForeignKey, String, DATE, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity
    from .user import User


class Kid(BaseModel):
    """Kid model."""

    __tablename__ = "kids"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    dob: Mapped[date] = mapped_column(DATE, nullable=True)
    interests: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    special_needs: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#a7f3d0", nullable=False)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    parent: Mapped["User"] = relationship("User", back_populates="kids")
    assigned_activities: Mapped[List["Activity"]] = relationship(
        "Activity",
        foreign_keys="Activity.assigned_to_kid_id",
        back_populates="assigned_to_kid",
        cascade="all, delete-orphan",
    )

    @property
    def age(self) -> int | None:
        """Calculate age in years based on date of birth."""
        if self.dob is None:
            return None
        today = date.today()
        return (
            today.year
            - self.dob.year
            - ((today.month, today.day) < (self.dob.month, self.dob.day))
        )

    def __repr__(self) -> str:
        return f"<Kid(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
