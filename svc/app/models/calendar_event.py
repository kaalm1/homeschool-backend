from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import ItemStatus
from svc.app.models.base import BaseModel

if TYPE_CHECKING:
    from svc.app.models.user import User

# Define PostgreSQL ENUM
calendar_status_enum = ENUM(ItemStatus, name="calendar_status_enum", create_type=True)


class CalendarEvent(BaseModel):
    """Calendar event model"""

    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    start_time: Mapped[datetime] = mapped_column(nullable=False, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    all_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[ItemStatus] = mapped_column(
        calendar_status_enum, default=ItemStatus.PENDING, nullable=False, index=True
    )

    reminder_minutes: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Minutes before event to send reminder"
    )

    # Meeting/Event specific fields
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attendees: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="RRULE format for recurring events"
    )

    # Foreign key to User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="calendar_events")

    def mark_completed(self) -> None:
        """Mark as completed"""
        self.status = ItemStatus.COMPLETED

    def mark_deleted(self) -> None:
        """Mark as deleted"""
        self.status = ItemStatus.DELETED

    def is_past(self) -> bool:
        """Check if event is in the past"""
        end = self.end_time or self.start_time
        return end < datetime.utcnow()

    def is_upcoming(self) -> bool:
        """Check if event is upcoming (within next 24 hours)"""
        if self.start_time > datetime.utcnow():
            time_diff = (self.start_time - datetime.utcnow()).total_seconds()
            return time_diff <= 86400  # 24 hours in seconds
        return False

    def __repr__(self) -> str:
        return f"<CalendarEvent(id={self.id}, title='{self.title}', start='{self.start_time}')>"
