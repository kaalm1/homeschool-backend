from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from svc.app.datatypes.week_activity import WeekActivityCreate

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

    llm_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_suggestion: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Seeded from ``Activity`` but can be different
    equipment: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    equipment_done: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )

    instructions: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    instructions_done: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )

    adhd_tips: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )
    adhd_tips_done: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(String), nullable=True, default=list
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="week_activities")
    activity: Mapped["Activity"] = relationship(
        "Activity", back_populates="week_assignments"
    )

    @validates("equipment_done", "instructions_done", "adhd_tips_done")
    def validate_subset(self, key, value):
        """Ensure *_done is a subset of the corresponding list."""
        base_field = key.replace("_done", "")
        base_list = getattr(self, base_field) or []
        done_list = value or []

        invalid = [item for item in done_list if item not in base_list]
        if invalid:
            raise ValueError(
                f"Invalid {key}: {invalid} not found in {base_field} {base_list}"
            )
        return value

    @classmethod
    def assign(
        cls,
        user_id: int,
        date_obj: date,
        week_activity_data: WeekActivityCreate,
    ) -> "WeekActivity":
        """Build WeekActivity from WeekActivityCreate plus system fields."""
        year, week, _ = date_obj.isocalendar()

        # turn Pydantic into dict and drop `None`/empty values
        base_data = week_activity_data.model_dump(exclude_none=True)

        # keep only keys that exist in the SQLAlchemy model
        valid_keys = set(cls.__table__.columns.keys())
        filtered_data = {k: v for k, v in base_data.items() if k in valid_keys}
        return cls(
            **filtered_data,
            user_id=user_id,
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
        # Status and rating first
        status = "✅" if getattr(self, "completed", False) else "⬜"
        rating = getattr(self, "rating", None)
        rating_str = f" (⭐{rating})" if rating else ""

        # Build a dict of column values dynamically
        col_values = {}
        for col in self.__table__.columns:
            if col.name in ("completed", "rating"):
                continue  # already handled
            value = getattr(self, col.name)
            # For long lists/strings, show a preview
            if isinstance(value, list) and len(value) > 3:
                value = f"[{', '.join(map(str, value[:3]))}...]"
            elif isinstance(value, str) and len(value) > 30:
                value = value[:27] + "..."
            col_values[col.name] = value

        cols_str = ", ".join(f"{k}={v!r}" for k, v in col_values.items())
        return f"<WeekActivity({status} {cols_str}{rating_str})>"
