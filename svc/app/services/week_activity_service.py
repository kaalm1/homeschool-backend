from datetime import date
from typing import List, Optional

from fastapi import HTTPException, status

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.dal.activity_suggestion_repository import ActivitySuggestionRepository
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
        suggestion_repo: Optional[ActivitySuggestionRepository] = None,
    ):
        self.week_activity_repo = week_activity_repo
        self.user_repo = user_repo
        self.activity_repo = activity_repo
        self.suggestion_repo = suggestion_repo

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

        # Merge Activity defaults into assignment if missing
        wa_data = week_activity_data.model_dump()
        for field in ("equipment", "instructions", "adhd_tips"):
            if not wa_data.get(field):
                wa_data[field] = getattr(activity, field) or []

        try:
            week_activity = self.week_activity_repo.create_week_activity(
                user_id, wa_data
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
        """Delete a week activity assignment and update AI suggestions if applicable."""
        # Get the activity before deletion to check if it was AI-suggested
        week_activity = self.week_activity_repo.get(week_activity_id)
        if not week_activity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Week activity not found"
            )

        # Check if this was an AI suggestion and mark it as removed
        if self.suggestion_repo:
            self._mark_suggestion_as_removed(week_activity)

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
        # Validate user exists
        user = self.user_repo.get(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found",
            )

        enriched_assignments: list[WeekActivityCreate] = []

        # Validate and enrich assignments
        for assignment in bulk_data.assignments:
            activity = self.activity_repo.get(assignment.activity_id)
            if not activity:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Activity with id {assignment.activity_id} not found",
                )

            # Merge Activity defaults into assignment if missing
            assignment_data = assignment.model_dump()
            for field in ("equipment", "instructions", "adhd_tips"):
                if not assignment_data.get(field):
                    assignment_data[field] = getattr(activity, field) or []

            enriched_assignments.append(WeekActivityCreate(**assignment_data))

        # Create all week activities
        try:
            week_activities = self.week_activity_repo.bulk_create_week_activities(
                user_id, enriched_assignments
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
            llm_notes=week_activity.llm_notes,
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
            activity_equipment=(
                week_activity.activity.equipment
                if hasattr(week_activity, "activity") and week_activity.activity
                else None
            ),
            activity_instructions=(
                week_activity.activity.instructions
                if hasattr(week_activity, "activity") and week_activity.activity
                else None
            ),
            activity_adhd_tips=(
                week_activity.activity.adhd_tips
                if hasattr(week_activity, "activity") and week_activity.activity
                else None
            ),
        )

    def _mark_suggestion_as_removed(self, week_activity) -> None:
        """Mark an AI suggestion as explicitly removed by the user."""
        if not self.suggestion_repo:
            return

        # Calculate the start date of the week
        target_week_start = date.fromisocalendar(
            week_activity.year, week_activity.week, 1
        )

        # Find matching suggestion
        suggestion = self.suggestion_repo.get_suggestion_by_params(
            user_id=week_activity.user_id,
            activity_id=week_activity.activity_id,
            target_week_start=target_week_start,
        )

        if suggestion:
            # Update the suggestion to mark it as explicitly removed
            self.suggestion_repo.update_suggestion_status(
                suggestion.id,
                completion_status="explicitly_removed",
                completion_date=date.today(),
                user_feedback="User removed this activity from their week plan",
            )

    def _update_suggestion_completion(
        self, week_activity, update_data: WeekActivityUpdate
    ) -> None:
        """Update AI suggestion when activity is completed."""
        if not self.suggestion_repo:
            return

        # Calculate the start date of the week
        target_week_start = date.fromisocalendar(
            week_activity.year, week_activity.week, 1
        )

        # Find matching suggestion
        suggestion = self.suggestion_repo.get_suggestion_by_params(
            user_id=week_activity.user_id,
            activity_id=week_activity.activity_id,
            target_week_start=target_week_start,
        )

        if suggestion:
            # Update the suggestion with completion info
            completion_status = "completed" if update_data.completed else "pending"
            self.suggestion_repo.update_suggestion_status(
                suggestion.id,
                completion_status=completion_status,
                completion_date=date.today() if update_data.completed else None,
                user_rating=update_data.rating,
                user_feedback=update_data.notes,
            )

    def create_weekly_activities_llm(self):
        pass
