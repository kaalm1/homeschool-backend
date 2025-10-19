from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.datatypes.enums import ItemStatus
from svc.app.models.calendar_event import CalendarEvent


class CalendarRepository(BaseRepository[CalendarEvent]):
    """Calendar repository with calendar-specific operations"""

    def __init__(self, db: Session):
        super().__init__(db, CalendarEvent)

    def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CalendarEvent]:
        """Get all calendar events for a user"""
        return self.get_many_by_field("user_id", user_id, skip, limit)

    def get_upcoming_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CalendarEvent]:
        """Get upcoming events for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.start_time >= datetime.utcnow(),
                self.model.status == ItemStatus.PENDING,
            )
            .order_by(self.model.start_time)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_past_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[CalendarEvent]:
        """Get past events for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id, self.model.start_time < datetime.utcnow()
            )
            .order_by(self.model.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_today_by_user(self, user_id: int) -> List[CalendarEvent]:
        """Get today's events for a user"""
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = today_start + timedelta(days=1)

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.start_time >= today_start,
                self.model.start_time < today_end,
                self.model.status == ItemStatus.PENDING,
            )
            .order_by(self.model.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_date_range(
        self, user_id: int, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        """Get events within a date range for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.start_time >= start_date,
                self.model.start_time <= end_date,
                self.model.status != ItemStatus.DELETED,
            )
            .order_by(self.model.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def get_upcoming_within_hours(
        self, user_id: int, hours: int = 24
    ) -> List[CalendarEvent]:
        """Get events within specified hours for a user"""
        future_time = datetime.utcnow() + timedelta(hours=hours)

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.start_time.between(datetime.utcnow(), future_time),
                self.model.status == ItemStatus.PENDING,
            )
            .order_by(self.model.start_time)
        )
        return list(self.db.scalars(stmt).all())

    def create_event(
        self,
        user_id: int,
        title: str,
        start_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        end_time: Optional[datetime] = None,
        all_day: bool = False,
        reminder_minutes: Optional[int] = None,
        url: Optional[str] = None,
        attendees: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_rule: Optional[str] = None,
    ) -> CalendarEvent:
        """Create a new calendar event for a user"""
        return self.create(
            {
                "user_id": user_id,
                "title": title,
                "description": description,
                "location": location,
                "start_time": start_time,
                "end_time": end_time,
                "all_day": all_day,
                "reminder_minutes": reminder_minutes,
                "url": url,
                "attendees": attendees,
                "is_recurring": is_recurring,
                "recurrence_rule": recurrence_rule,
                "status": ItemStatus.PENDING,
            }
        )

    def mark_completed(self, event_id: int) -> Optional[CalendarEvent]:
        """Mark a calendar event as completed"""
        event = self.get(event_id)
        if not event:
            return None

        event.mark_completed()
        self.db.commit()
        self.db.refresh(event)
        return event

    def mark_deleted(self, event_id: int) -> Optional[CalendarEvent]:
        """Soft delete a calendar event"""
        event = self.get(event_id)
        if not event:
            return None

        event.mark_deleted()
        self.db.commit()
        self.db.refresh(event)
        return event

    def count_upcoming_by_user(self, user_id: int) -> int:
        """Count upcoming events for a user"""
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.start_time >= datetime.utcnow(),
            self.model.status == ItemStatus.PENDING,
        )
        return len(list(self.db.scalars(stmt).all()))
