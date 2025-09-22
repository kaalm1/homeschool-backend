from datetime import date, datetime, timedelta
from typing import List, Optional

from pydantic import BaseModel, Field, validator


def get_current_week_monday() -> date:
    today = date.today()
    return today - timedelta(days=today.weekday())


class PlanWeekActivityRequest(BaseModel):
    location: str = Field()
    additional_notes: Optional[str] = Field(default=None)
    target_week_start: Optional[date] = Field(
        default_factory=get_current_week_monday,
        description="Start date of the week to plan (defaults to current week Monday)",
    )


class WeekActivityCreate(BaseModel):
    """Create a new week activity assignment."""

    activity_id: int = Field(..., description="ID of the activity")
    activity_date: Optional[date] = Field(
        default=None, description="Date for the week (defaults to current date)"
    )
    activity_week: Optional[int] = Field(
        default=None, description="Week of the activity"
    )
    activity_year: Optional[int] = Field(
        default=None, description="Year of the activity"
    )
    llm_suggestion: Optional[bool] = Field(default=None)
    llm_notes: Optional[str] = Field(default=None)


class WeekActivityUpdate(BaseModel):
    """Update completion status and rating for a week activity."""

    completed: Optional[bool] = Field(
        default=None, description="Whether the activity was completed"
    )
    rating: Optional[int] = Field(
        default=None, ge=1, le=5, description="Rating from 1-5 stars"
    )
    llm_notes: Optional[str] = Field(
        default=None, max_length=500, description="Optional notes about the experience"
    )
    notes: Optional[str] = Field(
        default=None, max_length=500, description="Optional notes about the experience"
    )

    @validator("rating")
    def validate_rating(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v


class WeekActivityResponse(BaseModel):
    """Response model for week activity."""

    id: int
    user_id: int
    activity_id: int
    year: int
    week: int
    completed: bool
    completed_at: Optional[datetime] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    llm_notes: Optional[str] = None

    # Unique to this week, takes default from activity, but will be its own
    # Since they can "checkmark" or change it
    equipment: Optional[List[str]] = None
    instructions: Optional[List[str]] = None
    adhd_tips: Optional[List[str]] = None

    # Include related activity and user info
    activity_title: Optional[str] = None
    activity_description: Optional[str] = None
    activity_equipment: Optional[List[str]] = None
    activity_instructions: Optional[List[str]] = None
    activity_adhd_tips: Optional[List[str]] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class WeekSummary(BaseModel):
    """Summary of activities for a specific week."""

    year: int
    week: int
    start_date: date
    end_date: date
    activities: list[WeekActivityResponse]

    # Summary stats
    total_activities: int
    completed_activities: int
    completion_rate: float
    average_rating: Optional[float]


class WeekRange(BaseModel):
    """Query parameters for week range."""

    year: Optional[int] = Field(
        default=None, description="Year (defaults to current year)"
    )
    week: Optional[int] = Field(
        default=None, description="Week number (defaults to current week)"
    )


class BulkWeekActivityCreate(BaseModel):
    """Create multiple week activities at once."""

    assignments: list[WeekActivityCreate]
