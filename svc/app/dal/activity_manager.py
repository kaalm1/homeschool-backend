from typing import List, Optional

from svc.app.models.activity import Activity


class ActivityManager:
    """Helper class for activity-related database operations."""

    def __init__(self, session):
        self.session = session

    def get_family_activities(self, user_id: int) -> List[Activity]:
        """Get activities assigned to the family level (not to any specific kid)."""
        return (
            self.session.query(Activity)
            .filter(Activity.user_id == user_id, Activity.assigned_to_kid_id.is_(None))
            .all()
        )

    def get_kid_activities(self, kid_id: int) -> List[Activity]:
        """Get activities assigned to a specific kid."""
        return (
            self.session.query(Activity)
            .filter(Activity.assigned_to_kid_id == kid_id)
            .all()
        )

    def get_all_user_activities(
        self, user_id: int, include_kid_activities: bool = False
    ) -> List[Activity]:
        """
        Get activities for a user/family.

        Args:
            user_id: The user/family ID
            include_kid_activities: If True, includes kid-specific activities too
        """
        query = self.session.query(Activity).filter(Activity.user_id == user_id)

        if not include_kid_activities:
            query = query.filter(Activity.assigned_to_kid_id.is_(None))

        return query.all()

    def get_activities_for_context(
        self, user_id: int, kid_id: Optional[int] = None
    ) -> List[Activity]:
        """
        Get activities appropriate for the viewing context.

        Args:
            user_id: The user/family ID
            kid_id: If provided, gets kid-specific activities. If None, gets family activities.

        Returns:
            Activities appropriate for the context
        """
        if kid_id:
            # Kid context: only activities assigned to this specific kid
            return self.get_kid_activities(kid_id)
        else:
            # Family context: only family-level activities
            return self.get_family_activities(user_id)

    def create_family_activity(self, user_id: int, title: str, **kwargs) -> Activity:
        """Create a new family-level activity."""
        activity = Activity(
            user_id=user_id,
            assigned_to_kid_id=None,  # Family level
            title=title,
            **kwargs,
        )
        self.session.add(activity)
        return activity

    def create_kid_activity(
        self, user_id: int, kid_id: int, title: str, **kwargs
    ) -> Activity:
        """Create a new kid-specific activity."""
        activity = Activity(
            user_id=user_id, assigned_to_kid_id=kid_id, title=title, **kwargs
        )
        self.session.add(activity)
        return activity

    def reassign_activity(
        self, activity_id: int, new_kid_id: Optional[int] = None
    ) -> Activity:
        """
        Reassign an activity to a different kid or back to family level.

        Args:
            activity_id: The activity to reassign
            new_kid_id: Kid to assign to, or None for family level
        """
        activity = self.session.query(Activity).get(activity_id)
        if activity:
            activity.assigned_to_kid_id = new_kid_id
        return activity
