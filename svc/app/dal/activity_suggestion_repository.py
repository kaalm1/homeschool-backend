from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload

from svc.app.dal.base_repository import BaseRepository
from svc.app.models.activity_suggestion import ActivitySuggestion


class ActivitySuggestionRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, ActivitySuggestion)

    def get_user_suggestions(
        self, user_id: int, lookback_weeks: int = 8, include_activity_data: bool = True
    ) -> List[ActivitySuggestion]:
        cutoff_date = datetime.now().date() - timedelta(weeks=lookback_weeks)
        query = (
            self.db.query(ActivitySuggestion)
            .filter(
                and_(
                    ActivitySuggestion.user_id == user_id,
                    ActivitySuggestion.suggested_date >= cutoff_date,
                )
            )
            .order_by(desc(ActivitySuggestion.suggested_date))
        )

        if include_activity_data:
            query = query.options(joinedload(ActivitySuggestion.activity))

        return query.all()

    def update_completion_status(
        self,
        suggestion_id: int,
        status: str,
        completion_date: Optional[date] = None,
        user_feedback: Optional[str] = None,
        user_rating: Optional[int] = None,
    ) -> ActivitySuggestion:
        suggestion = self.db.query(ActivitySuggestion).get(suggestion_id)
        if not suggestion:
            raise ValueError(f"Suggestion {suggestion_id} not found")

        suggestion.completion_status = status
        suggestion.completion_date = completion_date
        suggestion.user_feedback = user_feedback
        suggestion.user_rating = user_rating
        suggestion.updated_at = datetime.utcnow()

        self.db.commit()
        return suggestion

    def get_activity_suggestion_stats(
        self, activity_id: int, user_id: Optional[int] = None
    ) -> dict:
        """Get completion statistics for an activity."""
        query = self.db.query(ActivitySuggestion).filter(
            ActivitySuggestion.activity_id == activity_id
        )

        if user_id:
            query = query.filter(ActivitySuggestion.user_id == user_id)

        suggestions = query.all()

        if not suggestions:
            return {"total": 0, "completed": 0, "completion_rate": 0.0}

        completed = sum(
            1
            for s in suggestions
            if s.completion_status in ["completed", "likely_completed"]
        )

        return {
            "total": len(suggestions),
            "completed": completed,
            "completion_rate": completed / len(suggestions) if suggestions else 0.0,
            "last_suggested": max(s.suggested_date for s in suggestions),
            "avg_rating": (
                sum(s.user_rating for s in suggestions if s.user_rating)
                / len([s for s in suggestions if s.user_rating])
                if any(s.user_rating for s in suggestions)
                else None
            ),
        }

    def get_activities_suggested_for_week(
        self, user_id: int, target_week_start: date
    ) -> List[ActivitySuggestion]:
        """Get all activity suggestions for a specific user and target week."""
        return (
            self.db.query(ActivitySuggestion)
            .filter(
                ActivitySuggestion.user_id == user_id,
                ActivitySuggestion.target_week_start == target_week_start,
            )
            .all()
        )

    def get_suggestion_by_params(
        self, user_id: int, activity_id: int, target_week_start: date
    ) -> Optional[ActivitySuggestion]:
        """Find a suggestion by user, activity, and target week."""
        return (
            self.db.query(ActivitySuggestion)
            .filter(
                ActivitySuggestion.user_id == user_id,
                ActivitySuggestion.activity_id == activity_id,
                ActivitySuggestion.target_week_start == target_week_start,
            )
            .first()
        )

    def update_suggestion_status(
        self,
        suggestion_id: int,
        completion_status: str,
        completion_date: Optional[date] = None,
        user_rating: Optional[int] = None,
        user_feedback: Optional[str] = None,
    ) -> Optional[ActivitySuggestion]:
        """Update suggestion completion status and feedback."""
        suggestion = (
            self.db.query(ActivitySuggestion)
            .filter(ActivitySuggestion.id == suggestion_id)
            .first()
        )

        if not suggestion:
            return None

        suggestion.completion_status = completion_status
        if completion_date:
            suggestion.completion_date = completion_date
        if user_rating is not None:
            suggestion.user_rating = user_rating
        if user_feedback is not None:
            suggestion.user_feedback = user_feedback

        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def create_suggestions(self, suggestions_data: list) -> list[ActivitySuggestion]:
        """Create multiple suggestions at once."""
        suggestions = []
        for data in suggestions_data:
            suggestion = ActivitySuggestion(**data)
            self.db.add(suggestion)
            suggestions.append(suggestion)

        self.db.commit()
        for suggestion in suggestions:
            self.db.refresh(suggestion)

        return suggestions
