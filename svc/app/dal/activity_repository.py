from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models.activity import Activity
from ..models.kid import Kid
from .base_repository import BaseRepository


class ActivityRepository(BaseRepository[Activity]):
    """Activity repository with activity-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db, Activity)

    def get_by_parent_id(self, parent_id: int) -> List[Activity]:
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

    def create_activity(self, title: str, subject: str, kid_id: int) -> Activity:
        """Create a new activity."""
        return self.create(
            {"title": title, "subject": subject, "kid_id": kid_id, "done": False}
        )

    def toggle_done_status(self, activity_id: int) -> Activity:
        """Toggle the done status of an activity."""
        activity = self.get(activity_id)
        if activity:
            return self.update(activity_id, {"done": not activity.done})
        return None

    def get_completed_count_by_kid(self, kid_id: int) -> int:
        """Get count of completed activities for a kid."""
        return self.count({"kid_id": kid_id, "done": True})

    def get_activity_by_parent(self, activity_id: int, parent_id: int) -> Activity:
        """Get activity by ID and parent ID for security."""
        return self.db.execute(
            select(Activity)
            .join(Kid)
            .where(Activity.id == activity_id, Kid.parent_id == parent_id)
            .options(joinedload(Activity.kid))
        ).scalar_one_or_none()
