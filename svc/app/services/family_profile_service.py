import logging
from datetime import timedelta
from typing import Any, Dict

from svc.app.dal.family_preference_repository import FamilyPreferenceRepository
from svc.app.dal.user_behavior_analytic_repository import (
    UserBehaviorAnalyticsRepository,
)
from svc.app.dal.user_repository import UserRepository
from svc.app.datatypes.enums import Cost, NewExperienceOpenness
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.models.kid import Kid
from svc.app.models.user import User
from svc.app.services.family_preference_service import FamilyPreferenceService
from svc.app.services.kid_service import KidService

logger = logging.getLogger(__name__)


class FamilyProfileService:
    def __init__(
        self,
        user_repo: UserRepository,
        kid_service: "KidService",
        family_preference_service: FamilyPreferenceService,
    ):
        self.user_repo = user_repo
        self.kid_service = kid_service
        self.family_preference_service = family_preference_service

    def get_family_profile(self, user_id: int) -> FamilyProfile:
        """Get complete family profile with smart defaults."""
        user = self.user_repo.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Use the new preference service
        preferences_data = self.family_preference_service.get_family_preferences(
            user_id
        )
        kids = self.kid_service.kid_repo.get_by_parent_id(user_id)

        return FamilyProfile(
            # Core demographics from User model
            family_size=user.family_size or 1,
            adults_count=getattr(user, "adults_count", 1),
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
            preferred_cost_ranges=preferences_data.get(
                "preferred_cost_ranges", [Cost.FREE, Cost.LOW]
            ),
            # Time & Preferences
            available_days=preferences_data.get("available_days", []),
            preferred_time_slots=preferences_data.get("preferred_time_slots", []),
            max_activities_per_week=user.max_activities_per_week,
            preferred_themes=preferences_data.get("preferred_themes", []),
            preferred_activity_types=preferences_data.get(
                "preferred_activity_types", []
            ),
            group_activity_comfort=preferences_data.get(
                "group_activity_comfort",
            ),
            new_experience_openness=preferences_data.get(
                "new_experience_openness", NewExperienceOpenness.MODERATE
            ),
        )

    def update_family_demographics(self, user_id: int, demographics: dict) -> User:
        """Update core family demographics on User model."""
        return self.user_repo.update_family_profile(user_id, demographics)

    def update_family_preferences(
        self, user_id: int, preferences: dict
    ) -> Dict[str, Any]:
        """Update family preferences using the new service."""
        return self.family_preference_service.update_family_preferences(
            user_id, preferences
        )

    def partial_update_family_preferences(
        self, user_id: int, preferences: dict
    ) -> Dict[str, Any]:
        """Partially update family preferences using the new service."""
        return self.family_preference_service.partial_update_family_preferences(
            user_id, preferences
        )

    def reset_family_preferences(self, user_id: int) -> None:
        """Reset family preferences to defaults using the new service."""
        return self.family_preference_service.reset_family_preferences(user_id)

    def _kid_to_dict(self, kid: Kid) -> dict:
        """Convert Kid model to dictionary format."""
        return {
            "id": kid.id,
            "age": kid.age,
            "interests": kid.interests or [],
            "special_needs": kid.special_needs,
        }
