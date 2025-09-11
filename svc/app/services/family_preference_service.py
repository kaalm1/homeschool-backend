from datetime import datetime
from typing import Any, Dict

from sqlalchemy.exc import SQLAlchemyError

from svc.app.dal.family_preference_repository import FamilyPreferenceRepository
from svc.app.dal.user_repository import UserRepository  # <-- you’ll need this
from svc.app.datatypes.enums import (
    ActivityType,
    Cost,
    DaysOfWeek,
    GroupActivityComfort,
    Location,
    NewExperienceOpenness,
    PreferredTimeSlot,
    Theme,
)
from svc.app.models.family_preference import FamilyPreference


class FamilyPreferenceService:
    """Service for managing family preferences."""

    def __init__(
        self,
        family_preference_repository: FamilyPreferenceRepository,
        user_repository: UserRepository,
    ):
        self.family_preference_repo = family_preference_repository
        self.user_repo = user_repository

    def get_family_preferences(self, user_id: int) -> Dict[str, Any]:
        """Get family preferences for a user with smart defaults."""
        if not self.user_repo.exists(user_id):
            raise ValueError(f"User with ID {user_id} not found")

        preferences = self.family_preference_repo.get_by_user_id(user_id)

        if preferences:
            return self._preferences_to_dict(preferences)
        else:
            return self._get_default_preferences(user_id)

    def update_family_preferences(
        self, user_id: int, preference_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update or create family preferences for a user."""
        if not self.user_repo.exists(user_id):
            raise ValueError(f"User with ID {user_id} not found")

        prepared_data = self._prepare_preference_data(preference_data)

        try:
            preferences = self.family_preference_repo.create_or_update(
                user_id, prepared_data
            )
            return self._preferences_to_dict(preferences)
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    def partial_update_family_preferences(
        self, user_id: int, partial_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Partially update family preferences (only provided fields)."""
        current_prefs = self.get_family_preferences(user_id)
        updated_data = {**current_prefs, **partial_data}
        return self.update_family_preferences(user_id, updated_data)

    def reset_family_preferences(self, user_id: int) -> None:
        """Reset family preferences to defaults by deleting custom preferences."""
        if not self.user_repo.exists(user_id):
            raise ValueError(f"User with ID {user_id} not found")

        try:
            self.family_preference_repo.delete_by_user_id(user_id)
        except SQLAlchemyError as e:
            raise Exception(f"Database error: {str(e)}")

    # ------------------ Helpers ------------------

    def _preferences_to_dict(self, preferences: FamilyPreference) -> Dict[str, Any]:
        return {
            "id": preferences.id,
            "user_id": preferences.user_id,
            "preferred_themes": preferences.preferred_themes or [],
            "preferred_activity_types": preferences.preferred_activity_types or [],
            "preferred_cost_ranges": preferences.preferred_cost_ranges or [],
            "preferred_locations": preferences.preferred_locations or [],
            "available_days": preferences.available_days or [],
            "preferred_time_slots": preferences.preferred_time_slots or [],
            "group_activity_comfort": preferences.group_activity_comfort or "medium",
            "new_experience_openness": preferences.new_experience_openness or "medium",
            "educational_priorities": preferences.educational_priorities or [],
            "equipment_owned": preferences.equipment_owned or [],
            "accessibility_needs": preferences.accessibility_needs or [],
            "special_requirements": preferences.special_requirements,
            "updated_at": preferences.updated_at,
        }

    def _get_default_preferences(self, user_id: int | None = None) -> Dict[str, Any]:
        return {
            "id": None,
            "user_id": user_id,
            "preferred_themes": [],
            "preferred_activity_types": [],
            "preferred_cost_ranges": ["FREE", "LOW"],
            "preferred_locations": [],
            "available_days": ["saturday", "sunday"],
            "preferred_time_slots": ["morning", "afternoon"],
            "group_activity_comfort": "medium",
            "new_experience_openness": "medium",
            "educational_priorities": [],
            "equipment_owned": [],
            "accessibility_needs": [],
            "special_requirements": None,
            "updated_at": None,
        }

    def _prepare_preference_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prepared_data = {}

        enum_array_fields = {
            "preferred_themes": Theme,
            "preferred_activity_types": ActivityType,
            "preferred_cost_ranges": Cost,
            "preferred_locations": Location,
            "available_days": DaysOfWeek,
            "preferred_time_slots": PreferredTimeSlot,
        }

        for field, enum_class in enum_array_fields.items():
            if field in data and data[field] is not None:
                validated_values = []
                for value in data[field]:
                    try:
                        enum_class(value)
                        validated_values.append(value)
                    except ValueError:
                        pass
                prepared_data[field] = validated_values if validated_values else None

        single_enum_fields = {
            "group_activity_comfort": GroupActivityComfort,
            "new_experience_openness": NewExperienceOpenness,
        }
        for field, enum_class in single_enum_fields.items():
            if field in data and data[field] is not None:
                try:
                    enum_class(data[field])
                    prepared_data[field] = data[field]
                except ValueError:
                    pass

        for field in [
            "educational_priorities",
            "equipment_owned",
            "accessibility_needs",
        ]:
            if field in data:
                prepared_data[field] = data[field]

        if "special_requirements" in data:
            prepared_data["special_requirements"] = data["special_requirements"]

        return prepared_data
