from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.dal.user_repository import UserRepository
from svc.app.dal.week_activity_repository import WeekActivityRepository
from svc.app.datatypes.week_activity import (
    BulkWeekActivityCreate,
    WeekActivityCreate,
    WeekActivityResponse,
    WeekActivityUpdate,
    WeekSummary,
)


class WeekActivityService:
    def __init__(
        self,
        week_activity_repo: WeekActivityRepository,
        user_repo: UserRepository,
        activity_repo: ActivityRepository,
    ):
        self.week_activity_repo = week_activity_repo
        self.user_repo = user_repo
        self.activity_repo = activity_repo

    def create_week_activity(
        self, user_id: int, week_activity_data: WeekActivityCreate
    ) -> WeekActivityResponse:
        """Create a new week activity assignment with validation."""
        # Validate that activity exists
        activity = self.activity_repo.get(week_activity_data.activity_id)
        if not activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Activity with id {week_activity_data.activity_id} not found",
            )

        try:
            week_activity = self.week_activity_repo.create_week_activity(
                user_id, week_activity_data
            )
            return self._convert_to_response(week_activity)
        except Exception as e:
            # Handle unique constraint violations
            if "uq_user_activity_week" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This activity is already assigned to this user for this week",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create week activity",
            )

    def update_week_activity(
        self, week_activity_id: int, update_data: WeekActivityUpdate
    ) -> WeekActivityResponse:
        """Update a week activity's completion status, rating, and notes."""
        week_activity = self.week_activity_repo.update_week_activity(
            week_activity_id, update_data
        )
        if not week_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Week activity not found"
            )
        return self._convert_to_response(week_activity)

    def toggle_week_activity(self, week_activity_id: int) -> WeekActivityResponse:
        """Toggle the completion status of a week activity."""
        # First get the current activity
        week_activity = self.week_activity_repo.get(week_activity_id)

        if not week_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Week activity not found"
            )

        # Toggle completion status
        update_data = WeekActivityUpdate(completed=not week_activity.completed)
        return self.update_week_activity(week_activity_id, update_data)

    def get_current_week_activities(
        self, user_id: Optional[int] = None
    ) -> List[WeekActivityResponse]:
        """Get activities for the current week."""
        week_activities = self.week_activity_repo.get_current_week_activities(
            user_id=user_id
        )
        return [self._convert_to_response(wa) for wa in week_activities]

    def get_week_activities(
        self,
        year: Optional[int] = None,
        week: Optional[int] = None,
        user_id: Optional[int] = None,
        completed_only: Optional[bool] = None,
    ) -> List[WeekActivityResponse]:
        """Get week activities with optional filters."""
        week_activities = self.week_activity_repo.get_week_activities(
            year=year, week=week, user_id=user_id, completed_only=completed_only
        )
        return [self._convert_to_response(wa) for wa in week_activities]

    def get_week_summary(
        self,
        year: Optional[int] = None,
        week: Optional[int] = None,
        user_id: Optional[int] = None,
    ) -> WeekSummary:
        """Get a summary of activities for a specific week (defaults to current week)."""
        if year is None or week is None:
            today = date.today()
            current_year, current_week, _ = today.isocalendar()
            year = year or current_year
            week = week or current_week

        return self.week_activity_repo.get_week_summary(
            year=year, week=week, user_id=user_id
        )

    def delete_week_activity(self, week_activity_id: int) -> bool:
        """Delete a week activity assignment."""
        success = self.week_activity_repo.delete_week_activity(week_activity_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Week activity not found"
            )
        return success

    def remove_activity_from_week(
        self,
        user_id: int,
        activity_id: int,
        year: Optional[int] = None,
        week: Optional[int] = None,
    ) -> bool:
        """Remove a specific activity from a user's week."""
        if year is None or week is None:
            today = date.today()
            current_year, current_week, _ = today.isocalendar()
            year = year or current_year
            week = week or current_week

        success = self.week_activity_repo.delete_week_activity_by_params(
            user_id=user_id, activity_id=activity_id, year=year, week=week
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Week activity assignment not found",
            )
        return success

    def get_available_weeks(self, user_id: Optional[int] = None) -> List[dict]:
        """Get all weeks that have activities."""
        weeks = self.week_activity_repo.get_weeks_with_activities(user_id=user_id)

        result = []
        for year, week in weeks:
            result.append(
                {"year": year, "week": week, "display": f"Week {week}, {year}"}
            )

        return result

    def bulk_create_week_activities(
        self, user_id: int, bulk_data: BulkWeekActivityCreate
    ) -> List[WeekActivityResponse]:
        """Create multiple week activities at once."""
        # Validate all assignments first
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        for assignment in bulk_data.assignments:
            activity = self.activity_repo.get(assignment.activity_id)
            if not activity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity with id {assignment.activity_id} not found",
                )

        try:
            week_activities = self.week_activity_repo.bulk_create_week_activities(
                user_id, bulk_data.assignments
            )
            return [self._convert_to_response(wa) for wa in week_activities]
        except Exception as e:
            if "uq_user_activity_week" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="One or more activities are already assigned for the specified weeks",
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create week activities",
            )

    def _convert_to_response(self, week_activity) -> WeekActivityResponse:
        """Convert a WeekActivity model to response format."""
        return WeekActivityResponse(
            id=week_activity.id,
            user_id=week_activity.user_id,
            activity_id=week_activity.activity_id,
            year=week_activity.year,
            week=week_activity.week,
            completed=week_activity.completed,
            completed_at=week_activity.completed_at,
            rating=week_activity.rating,
            notes=week_activity.notes,
            activity_title=(
                week_activity.activity.title
                if hasattr(week_activity, "activity") and week_activity.activity
                else None
            ),
            activity_description=(
                week_activity.activity.description
                if hasattr(week_activity, "activity") and week_activity.activity
                else None
            ),
        )

    def create_weekly_activities_llm(self):
        pass
