from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, String,
                        UniqueConstraint)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity
    from .user import User


class WeekActivity(BaseModel):
    """Links an activity to a specific user and ISO week (year + week number)."""

    __tablename__ = "week_activities"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "activity_id", "year", "week", name="uq_user_activity_week"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), index=True
    )

    year: Mapped[int] = mapped_column(Integer, nullable=False)
    week: Mapped[int] = mapped_column(Integer, nullable=False)  # ISO week number (1–53)

    # Completion and rating fields
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 scale
    notes: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Optional notes from user

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="week_activities")
    activity: Mapped["Activity"] = relationship(
        "Activity", back_populates="week_assignments"
    )

    @classmethod
    def assign(cls, user_id: int, activity_id: int, date_obj: date) -> "WeekActivity":
        year, week, _ = date_obj.isocalendar()
        return cls(
            user_id=user_id,
            activity_id=activity_id,
            year=year,
            week=week,
            completed=False,
        )

    def mark_completed(
        self, rating: Optional[int] = None, notes: Optional[str] = None
    ) -> None:
        """Mark the activity as completed with optional rating and notes."""
        self.completed = True
        self.completed_at = datetime.utcnow()
        if rating is not None:
            if not (1 <= rating <= 5):
                raise ValueError("Rating must be between 1 and 5")
            self.rating = rating
        if notes is not None:
            self.notes = notes

    def mark_incomplete(self) -> None:
        """Mark the activity as incomplete and clear completion data."""
        self.completed = False
        self.completed_at = None
        # Keep rating and notes for reference even when marked incomplete

    def __repr__(self) -> str:
        status = "✅" if self.completed else "⬜"
        rating_str = f" (⭐{self.rating})" if self.rating else ""
        return f"<WeekActivity({status} user_id={self.user_id}, activity_id={self.activity_id}, year={self.year}, week={self.week}{rating_str})>"
