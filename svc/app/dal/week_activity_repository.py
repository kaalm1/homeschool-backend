from datetime import date, datetime, timedelta
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload

from svc.app.dal.base_repository import BaseRepository
from svc.app.datatypes.week_activity import (
    WeekActivityCreate,
    WeekActivityResponse,
    WeekActivityUpdate,
    WeekSummary,
)
from svc.app.models.activity import Activity
from svc.app.models.user import User
from svc.app.models.week_activity import WeekActivity


class WeekActivityRepository(BaseRepository[WeekActivity]):
    """WeekActivity repository with week activity-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db, WeekActivity)

    def create_week_activity(
        self, user_id: int, week_activity_data: WeekActivityCreate
    ) -> WeekActivity:
        """Create a new week activity assignment."""
        if week_activity_data.activity_date:
            target_date = week_activity_data.date

        elif week_activity_data.activity_year and week_activity_data.activity_week:
            # ISO weeks start on Monday; this gets the Monday of the given ISO week
            target_date = datetime.strptime(
                f"{week_activity_data.activity_year}-W{week_activity_data.activity_week:02d}-1",
                "%G-W%V-%u",
            ).date()

        else:
            target_date = date.today()

        week_activity = WeekActivity.assign(
            user_id=user_id,
            activity_id=week_activity_data.activity_id,
            date_obj=target_date,
        )

        self.db.add(week_activity)
        self.db.commit()
        self.db.refresh(week_activity)
        return week_activity

    def update_week_activity(
        self, week_activity_id: int, update_data: WeekActivityUpdate
    ) -> Optional[WeekActivity]:
        """Update a week activity's completion status, rating, and notes."""
        week_activity = self.get(week_activity_id)
        if not week_activity:
            return None

        # Update fields if provided
        if update_data.completed is not None:
            if update_data.completed and not week_activity.completed:
                # Mark as completed with optional rating and notes
                week_activity.mark_completed(
                    rating=update_data.rating, notes=update_data.notes
                )
            elif not update_data.completed and week_activity.completed:
                # Mark as incomplete
                week_activity.mark_incomplete()

        # Update rating and notes even if completion status doesn't change
        if update_data.rating is not None:
            week_activity.rating = update_data.rating
        if update_data.notes is not None:
            week_activity.notes = update_data.notes

        self.db.commit()
        self.db.refresh(week_activity)
        return week_activity

    def get_week_activities(
        self,
        year: Optional[int] = None,
        week: Optional[int] = None,
        user_id: Optional[int] = None,
        completed_only: Optional[bool] = None,
    ) -> List[WeekActivity]:
        """Get week activities, optionally filtered by year, week, user, and completion status."""
        query = (
            self.db.execute(
                select(WeekActivity)
                .options(
                    joinedload(WeekActivity.activity), joinedload(WeekActivity.user)
                )
                .where(
                    *[
                        condition
                        for condition in [
                            WeekActivity.year == year if year is not None else None,
                            WeekActivity.week == week if week is not None else None,
                            (
                                WeekActivity.user_id == user_id
                                if user_id is not None
                                else None
                            ),
                            (
                                WeekActivity.completed == completed_only
                                if completed_only is not None
                                else None
                            ),
                        ]
                        if condition is not None
                    ]
                )
            )
            .scalars()
            .all()
        )
        return list(query)

    def get_current_week_activities(
        self, user_id: Optional[int] = None
    ) -> List[WeekActivity]:
        """Get activities for the current week."""
        today = date.today()
        year, week, _ = today.isocalendar()
        return self.get_week_activities(year=year, week=week, user_id=user_id)

    def get_week_summary(
        self, year: int, week: int, user_id: Optional[int] = None
    ) -> WeekSummary:
        """Get a summary of activities for a specific week."""
        activities = self.get_week_activities(year=year, week=week, user_id=user_id)

        # Calculate week start and end dates
        jan_4th = date(year, 1, 4)  # January 4th is always in week 1
        week_start = (
            jan_4th - timedelta(days=jan_4th.weekday()) + timedelta(weeks=week - 1)
        )
        week_end = week_start + timedelta(days=6)

        activity_responses = [
            WeekActivityResponse(
                id=wa.id,
                user_id=wa.user_id,
                activity_id=wa.activity_id,
                year=wa.year,
                week=wa.week,
                completed=wa.completed,
                completed_at=wa.completed_at,
                rating=wa.rating,
                notes=wa.notes,
                activity_title=wa.activity.title if wa.activity else None,
                activity_description=wa.activity.description if wa.activity else None,
            )
            for wa in activities
        ]

        # Calculate summary stats
        total_activities = len(activities)
        completed_activities = sum(1 for wa in activities if wa.completed)
        completion_rate = (
            (completed_activities / total_activities) if total_activities > 0 else 0.0
        )

        # Calculate average rating (only for completed activities with ratings)
        rated_activities = [
            wa for wa in activities if wa.completed and wa.rating is not None
        ]
        average_rating = (
            sum(wa.rating for wa in rated_activities) / len(rated_activities)
            if rated_activities
            else None
        )

        return WeekSummary(
            year=year,
            week=week,
            start_date=week_start,
            end_date=week_end,
            activities=activity_responses,
            total_activities=total_activities,
            completed_activities=completed_activities,
            completion_rate=completion_rate,
            average_rating=average_rating,
        )

    def delete_week_activity(self, week_activity_id: int) -> bool:
        """Delete a week activity assignment."""
        return self.delete(week_activity_id) is not None

    def delete_week_activity_by_params(
        self, user_id: int, activity_id: int, year: int, week: int
    ) -> bool:
        """Delete a week activity by user, activity, year, and week."""
        week_activity = self.db.execute(
            select(WeekActivity).where(
                and_(
                    WeekActivity.user_id == user_id,
                    WeekActivity.activity_id == activity_id,
                    WeekActivity.year == year,
                    WeekActivity.week == week,
                )
            )
        ).scalar_one_or_none()

        if week_activity:
            self.db.delete(week_activity)
            self.db.commit()
            return True
        return False

    def get_weeks_with_activities(
        self, user_id: Optional[int] = None
    ) -> List[tuple[int, int]]:
        """Get all year/week combinations that have activities."""
        query = select(WeekActivity.year, WeekActivity.week).distinct()

        if user_id is not None:
            query = query.where(WeekActivity.user_id == user_id)

        query = query.order_by(WeekActivity.year.desc(), WeekActivity.week.desc())

        result = self.db.execute(query).all()
        return [(year, week) for year, week in result]

    def bulk_create_week_activities(
        self, user_id: int, week_activities_data: List[WeekActivityCreate]
    ) -> List[WeekActivity]:
        """Create multiple week activities at once."""
        week_activities = []

        for wa_data in week_activities_data:
            if wa_data.activity_date:
                target_date = wa_data.date

            elif wa_data.activity_year and wa_data.activity_week:
                # ISO weeks start on Monday; this gets the Monday of the given ISO week
                target_date = datetime.strptime(
                    f"{wa_data.activity_year}-W{wa_data.activity_week:02d}-1",
                    "%G-W%V-%u",
                ).date()

            else:
                target_date = date.today()

            week_activity = WeekActivity.assign(
                user_id=user_id,
                activity_id=wa_data.activity_id,
                date_obj=target_date,
                llm_suggestion=wa_data.llm_suggestion,
                llm_notes=wa_data.llm_notes,
            )
            week_activities.append(week_activity)

        self.db.add_all(week_activities)
        self.db.commit()

        for wa in week_activities:
            self.db.refresh(wa)

        return week_activities

    def get_by_user_id(self, user_id: int) -> Sequence[WeekActivity]:
        """Get all week activities for a specific user."""
        return (
            self.db.execute(
                select(WeekActivity)
                .where(WeekActivity.user_id == user_id)
                .options(
                    joinedload(WeekActivity.activity), joinedload(WeekActivity.user)
                )
                .order_by(WeekActivity.year.desc(), WeekActivity.week.desc())
            )
            .scalars()
            .all()
        )

    def get_by_activity_id(self, activity_id: int) -> Sequence[WeekActivity]:
        """Get all week assignments for a specific activity."""
        return (
            self.db.execute(
                select(WeekActivity)
                .where(WeekActivity.activity_id == activity_id)
                .options(
                    joinedload(WeekActivity.activity), joinedload(WeekActivity.user)
                )
                .order_by(WeekActivity.year.desc(), WeekActivity.week.desc())
            )
            .scalars()
            .all()
        )

    def get_by_params(
        self, user_id: int, activity_id: int, year: int, week: int
    ) -> Optional[WeekActivity]:
        """Get a week activity by user, activity, year, and week parameters."""
        return (
            self.db.query(WeekActivity)
            .filter(
                WeekActivity.user_id == user_id,
                WeekActivity.activity_id == activity_id,
                WeekActivity.year == year,
                WeekActivity.week == week,
            )
            .first()
        )
