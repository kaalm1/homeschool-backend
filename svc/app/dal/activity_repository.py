from typing import List, Optional, Sequence, cast

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from ..datatypes.enums import (AgeGroup, Cost, Duration, Location,
                               Participants, Season)
from ..models.activity import Activity
from ..models.kid import Kid
from .base_repository import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    """Activity repository with activity-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db, Activity)

    # ---------------------------
    # Standard CRUD / helper methods
    # ---------------------------
    def get_by_parent_id(self, parent_id: int) -> Sequence[Activity]:
        """Get all activities for a parent."""
        return (
            self.db.execute(
                select(Activity)
                .where(Activity.user_id == parent_id)
                .options(joinedload(Activity.user))
            )
            .scalars()
            .all()
        )

    def get_by_kid_id(self, kid_id: int) -> List[Activity]:
        """Get all activities for a specific kid."""
        return self.get_all(filters={"kid_id": kid_id})

    def create_activity(self, title: str, user_id: int, **kwargs) -> Activity:
        """Create a new activity for a user/family."""
        activity_data = {"title": title, "user_id": user_id, "done": False, **kwargs}
        return self.create(activity_data)

    def create_tagged_activities(
        self, tagged_activities_data: List[dict], user_id: int
    ) -> List[Activity]:
        """Create multiple tagged activities from LLM response."""
        created_activities = []

        for activity_data in tagged_activities_data:
            # Extract the basic activity info
            activity_info = {
                "user_id": user_id,
                "done": False,
                **activity_data,
            }

            # Create the activity
            activity = self.create(activity_info)
            created_activities.append(activity)

        return created_activities

    def bulk_create_activities(self, activities_data: List[dict]) -> List[Activity]:
        """Bulk create activities for better performance."""
        activities = [Activity(**data) for data in activities_data]
        self.db.add_all(activities)
        self.db.commit()

        # Refresh all activities to get their IDs
        for activity in activities:
            self.db.refresh(activity)

        return activities

    def toggle_done_status(self, activity_id: int) -> Optional[Activity]:
        """Toggle the done status of an activity."""
        activity = self.get(activity_id)
        if activity:
            return self.update(activity_id, {"done": not activity.done})
        return None

    def get_completed_count_by_parent(self, parent_id: int) -> int:
        """Get count of completed activities for a parent/family."""
        return self.count({"user_id": parent_id, "done": True})

    def get_activity_by_parent(
        self, activity_id: int, parent_id: int
    ) -> Optional[Activity]:
        """Get activity by ID and parent ID for security."""
        return self.db.execute(
            select(Activity)
            .where(Activity.id == activity_id, Activity.user_id == parent_id)
            .options(joinedload(Activity.user))
        ).scalar_one_or_none()

    # ---------------------------
    # Flexible filter method
    # ---------------------------
    def filter_activities(
        self,
        parent_id: int,
        cost: Optional[List[Cost]] = None,
        duration: Optional[List[Duration]] = None,
        participants: Optional[List[Participants]] = None,
        locations: Optional[List[Location]] = None,
        seasons: Optional[List[Season]] = None,
        age_groups: Optional[List[AgeGroup]] = None,
        themes: Optional[List[str]] = None,
        activity_types: Optional[List[str]] = None,
    ) -> List[Activity]:
        """Flexible filter that supports enums + themes + activity types."""

        filters = []

        # ARRAY enums filtering
        if cost:
            filters.append(Activity.costs.overlap(cost))
        if duration:
            filters.append(Activity.durations.overlap(duration))
        if participants:
            filters.append(Activity.participants.overlap(participants))
        if locations:
            filters.append(Activity.locations.overlap(locations))
        if seasons:
            filters.append(Activity.seasons.overlap(seasons))
        if age_groups:
            filters.append(Activity.age_groups.overlap(age_groups))
        if themes:
            filters.append(Activity.themes.overlap(themes))
        if activity_types:
            filters.append(Activity.activity_types.overlap(activity_types))

        query = self.db.query(Activity).filter(Activity.user_id == parent_id).distinct()

        if filters:
            query = query.filter(and_(*filters))

        return cast(List[Activity], query.all())
