from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ARRAY, JSON, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity
    from .user import User


class ActivitySuggestion(BaseModel):
    """Track activity suggestions for learning and analytics."""

    __tablename__ = "activity_suggestions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Suggestion Context
    suggested_date: Mapped[date] = mapped_column(nullable=False, index=True)
    target_week_start: Mapped[date] = mapped_column(nullable=False, index=True)
    suggested_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Completion Tracking
    completion_status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )
    completion_date: Mapped[Optional[date]] = mapped_column(nullable=True)
    user_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_rating: Mapped[Optional[int]] = mapped_column(nullable=True)  # 1-5 stars

    # System Analytics
    inferred_completion_likelihood: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    weather_conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="activity_suggestions")
    activity: Mapped["Activity"] = relationship("Activity")

    __table_args__ = (
        Index("idx_activity_suggestions_user_date", "user_id", "suggested_date"),
        Index(
            "idx_activity_suggestions_activity_date", "activity_id", "suggested_date"
        ),
    )
