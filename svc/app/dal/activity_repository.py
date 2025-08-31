from typing import List, Optional, Sequence, cast

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from ..datatypes.enums import AgeGroup, Cost, Duration, Location, Participants, Season
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
        """Get all activities for a parent's kids."""
        return (
            self.db.execute(
                select(Activity)
                .join(Kid)
                .where(Kid.parent_id == parent_id)
                .options(joinedload(Activity.kid))
            )
            .scalars()
            .all()
        )

    def get_by_kid_id(self, kid_id: int) -> List[Activity]:
        """Get all activities for a specific kid."""
        return self.get_all(filters={"kid_id": kid_id})

    def create_activity(self, title: str, kid_id: int) -> Activity:
        """Create a new activity."""
        return self.create({"title": title, "kid_id": kid_id, "done": False})

    def toggle_done_status(self, activity_id: int) -> Optional[Activity]:
        """Toggle the done status of an activity."""
        activity = self.get(activity_id)
        if activity:
            return self.update(activity_id, {"done": not activity.done})
        return None

    def get_completed_count_by_kid(self, kid_id: int) -> int:
        """Get count of completed activities for a kid."""
        return self.count({"kid_id": kid_id, "done": True})

    def get_activity_by_parent(
        self, activity_id: int, parent_id: int
    ) -> Optional[Activity]:
        """Get activity by ID and parent ID for security."""
        return self.db.execute(
            select(Activity)
            .join(Kid)
            .where(Activity.id == activity_id, Kid.parent_id == parent_id)
            .options(joinedload(Activity.kid))
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

        query = (
            self.db.query(Activity)
            .join(Kid)
            .filter(Kid.parent_id == parent_id)
            .distinct()
        )

        if filters:
            query = query.filter(and_(*filters))

        return cast(List[Activity], query.all())
