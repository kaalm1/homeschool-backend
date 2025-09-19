import logging
from typing import List, Optional

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.data.generic_activities import GENERIC_FAMILY_ACTIVITIES
from svc.app.models.activity import Activity
from svc.app.models.user import User

logger = logging.getLogger(__name__)


class UserSeedingService:
    """Service for seeding initial data for new users."""

    def __init__(self, activity_repository: ActivityRepository):
        self.activity_repo = activity_repository

    def seed_new_user(self, user: User) -> dict:
        """
        Seed all initial data for a new user.
        Returns a summary of what was seeded.
        """
        seeding_summary = {"user_id": user.id, "activities_created": 0, "errors": []}

        try:
            # Seed activities
            activities_count = self._seed_activities(user)
            seeding_summary["activities_created"] = activities_count

            # Add other seeding methods here as your app grows
            # self._seed_default_preferences(user)
            # self._seed_welcome_messages(user)

            logger.info(
                f"Successfully seeded data for user {user.id}: {seeding_summary}"
            )

        except Exception as e:
            logger.exception(f"Failed to seed data for user {user.id}: {str(e)}")
            seeding_summary["errors"].append(error_msg)

        return seeding_summary

    def _seed_activities(self, user: User) -> int:
        """
        Seed default activities for a new user.
        Returns the number of activities created.
        """
        try:
            activities_data = self._prepare_activities_data(user)

            if not activities_data:
                logger.warning(f"No activities to seed for user {user.id}")
                return 0

            # Use bulk create for better performance
            created_activities = self.activity_repo.bulk_create_activities(
                activities_data
            )

            logger.info(
                f"Created {len(created_activities)} activities for user {user.id}"
            )
            return len(created_activities)

        except Exception as e:
            logger.exception(f"Failed to seed activities for user {user.id}: {str(e)}")
            raise

    def _prepare_activities_data(self, user: User) -> List[dict]:
        """Prepare activities data from generic templates."""
        activities_data = []

        for generic_activity in GENERIC_FAMILY_ACTIVITIES:
            activity_data = {
                "title": generic_activity.title,
                "description": generic_activity.description,
                "user_id": user.id,
                "assigned_to_kid_id": None,  # Will be assigned when kids are added
                "done": False,
                "llm_generated": False,
                "costs": generic_activity.costs,
                "durations": generic_activity.durations,
                "participants": generic_activity.participants,
                "locations": generic_activity.locations,
                "seasons": generic_activity.seasons,
                "age_groups": generic_activity.age_groups,
                "frequency": generic_activity.frequency,
                "themes": generic_activity.themes,
                "activity_types": generic_activity.activity_types,
                "primary_type": generic_activity.primary_type,
                "primary_theme": generic_activity.primary_theme,
                "activity_scale": generic_activity.activity_scale,
            }
            activities_data.append(activity_data)

        return activities_data

    def _seed_default_preferences(self, user: User) -> None:
        """Seed default user preferences (example for future use)."""
        # This is an example of how you might seed other types of data
        try:
            # Example: Create default user preferences
            default_preferences = {
                "notifications_enabled": True,
                "theme": "light",
                "default_activity_duration": "MEDIUM",
                "preferred_locations": ["HOME_INDOOR", "LOCAL"],
            }

            # You would implement this based on your preferences model
            # self.preferences_repo.create_user_preferences(user.id, default_preferences)

            logger.info(f"Created default preferences for user {user.id}")

        except Exception as e:
            logger.exception(f"Failed to seed preferences for user {user.id}: {str(e)}")
            raise

    def reseed_activities(self, user: User, overwrite: bool = False) -> int:
        """
        Reseed activities for an existing user.
        Useful for updating users with new generic activities.
        """
        try:
            if overwrite:
                # Delete existing activities (be careful with this!)
                existing_activities = self.activity_repo.get_by_parent_id(user.id)
                for activity in existing_activities:
                    if not activity.done:  # Don't delete completed activities
                        self.activity_repo.delete(activity.id)

            return self._seed_activities(user)

        except Exception as e:
            logger.exception(f"Failed to reseed activities for user {user.id}: {str(e)}")
            raise
