import logging
from datetime import timedelta

from svc.app.dal.family_preference_repository import FamilyPreferencesRepository
from svc.app.dal.user_behavior_analytic_repository import (
    UserBehaviorAnalyticsRepository,
)
from svc.app.dal.user_repository import UserRepository
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.services.kid_service import KidService

logger = logging.getLogger(__name__)


class FamilyProfileService:
    def __init__(
        self,
        user_repo: UserRepository,
        preferences_repo: FamilyPreferencesRepository,
        analytics_repo: UserBehaviorAnalyticsRepository,
        kid_service: "KidService",
    ):
        self.user_repo = user_repo
        self.preferences_repo = preferences_repo
        self.analytics_repo = analytics_repo
        self.kid_service = kid_service

    def get_family_profile(self, user_id: int) -> FamilyProfile:
        """Get complete family profile with smart defaults."""
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        preferences = self.preferences_repo.get_by_user(user_id)
        kids = self.kid_service.get_kids_by_parent(user_id)

        return FamilyProfile(
            # Core demographics from User model
            family_size=user.family_size or 1,
            adults_count=user.adults_count or 1,
            kids=[self._kid_to_dict(kid) for kid in kids],
            # Location
            home_location=user.location_for_llm or f"{user.city}, {user.state}",
            home_coordinates=(
                (user.latitude, user.longitude)
                if user.latitude and user.longitude
                else None
            ),
            max_travel_distance=user.max_travel_distance or 30,
            has_car=user.has_car,
            # Financial
            weekly_activity_budget=user.weekly_activity_budget,
            preferred_cost_ranges=(
                preferences.preferred_cost_ranges if preferences else ["FREE", "LOW"]
            ),
            # Time & Preferences
            available_days=(
                preferences.available_days if preferences else ["saturday", "sunday"]
            ),
            preferred_time_slots=(
                preferences.preferred_time_slots
                if preferences
                else ["morning", "afternoon"]
            ),
            max_activities_per_week=user.max_activities_per_week,
            preferred_themes=preferences.preferred_themes if preferences else [],
            preferred_activity_types=(
                preferences.preferred_activity_types if preferences else []
            ),
            group_activity_comfort=(
                preferences.group_activity_comfort if preferences else "medium"
            ),
            new_experience_openness=(
                preferences.new_experience_openness if preferences else "medium"
            ),
        )

    def update_family_demographics(self, user_id: int, demographics: dict) -> User:
        """Update core family demographics on User model."""
        return self.user_repo.update_family_profile(user_id, demographics)

    def update_family_preferences(
        self, user_id: int, preferences: dict
    ) -> FamilyPreferences:
        """Update family preferences."""
        return self.preferences_repo.create_or_update(user_id, preferences)

    def _kid_to_dict(self, kid) -> dict:
        return {
            "id": kid.id,
            "age": kid.age,
            "interests": kid.interests or [],
            "special_needs": kid.special_needs,
        }
