from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from svc.app.datatypes.common import TimestampMixin
from svc.app.datatypes.enums import ItemStatus


class CalendarBase(BaseModel):
    """Base calendar schema"""

    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, max_length=255, description="Event location")
    start_time: datetime = Field(..., description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    all_day: bool = Field(False, description="All day event")
    reminder_minutes: Optional[int] = Field(
        None, ge=0, description="Reminder minutes before event"
    )
    url: Optional[str] = Field(None, max_length=500, description="Meeting URL")
    attendees: Optional[str] = Field(None, description="Comma-separated attendees")
    is_recurring: bool = Field(False, description="Is recurring event")
    recurrence_rule: Optional[str] = Field(
        None, max_length=200, description="RRULE for recurrence"
    )

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate end_time is after start_time"""
        if v and "start_time" in info.data and v < info.data["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class CalendarCreate(CalendarBase):
    """Schema for creating calendar events"""

    pass


class CalendarUpdate(BaseModel):
    """Schema for updating calendar events"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=255)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    all_day: Optional[bool] = None
    reminder_minutes: Optional[int] = Field(None, ge=0)
    url: Optional[str] = Field(None, max_length=500)
    attendees: Optional[str] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = Field(None, max_length=200)
    status: Optional[ItemStatus] = None


class CalendarResponse(CalendarBase, TimestampMixin):
    """Schema for calendar responses"""

    id: int = Field(..., description="Event ID")
    status: ItemStatus = Field(..., description="Event status")
    is_past: bool = Field(False, description="Whether event is in the past")
    is_upcoming: bool = Field(False, description="Whether event is within 24 hours")

    class Config:
        from_attributes = True


class ParsedCalendar(BaseModel):
    """Parsed calendar event from AI"""

    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str
    end_time: Optional[str] = None
    all_day: bool = False
    reminder_minutes: Optional[int] = None
    url: Optional[str] = None
    attendees: Optional[str] = None


class CalendarSummary(BaseModel):
    """Summary statistics for calendar"""

    total: int = Field(..., description="Total events")
    upcoming: int = Field(..., description="Upcoming events")
    past: int = Field(..., description="Past events")
    today: int = Field(..., description="Events today")
