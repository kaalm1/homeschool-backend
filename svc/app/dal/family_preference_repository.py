from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from svc.app.models.family_preference import FamilyPreference


class FamilyPreferenceRepository:
    """Repository for family preference data access operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> Optional[FamilyPreference]:
        """
        Get family preferences by user ID.

        Args:
            user_id: The user's ID

        Returns:
            FamilyPreference instance or None if not found
        """
        return (
            self.db.query(FamilyPreference)
            .filter(FamilyPreference.user_id == user_id)
            .first()
        )

    def create(self, user_id: int, preference_data: Dict[str, Any]) -> FamilyPreference:
        """
        Create new family preferences.

        Args:
            user_id: The user's ID
            preference_data: Dictionary containing preference data

        Returns:
            Created FamilyPreference instance
        """
        try:
            preference = FamilyPreference(
                user_id=user_id, updated_at=datetime.utcnow(), **preference_data
            )
            self.db.add(preference)
            self.db.commit()
            self.db.refresh(preference)

            return preference

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to create family preferences: {str(e)}")

    def update(
        self, preference_id: int, preference_data: Dict[str, Any]
    ) -> Optional[FamilyPreference]:
        """
        Update existing family preferences.

        Args:
            preference_id: The preference record ID
            preference_data: Dictionary containing updated preference data

        Returns:
            Updated FamilyPreference instance or None if not found
        """
        try:
            preference = (
                self.db.query(FamilyPreference)
                .filter(FamilyPreference.id == preference_id)
                .first()
            )

            if not preference:
                return None

            # Update fields
            for field, value in preference_data.items():
                if hasattr(preference, field):
                    setattr(preference, field, value)

            preference.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(preference)

            return preference

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(f"Failed to update family preferences: {str(e)}")

    def update_by_user_id(
        self, user_id: int, preference_data: Dict[str, Any]
    ) -> Optional[FamilyPreference]:
        """
        Update family preferences by user ID.

        Args:
            user_id: The user's ID
            preference_data: Dictionary containing updated preference data

        Returns:
            Updated FamilyPreference instance or None if not found
        """
        try:
            preference = self.get_by_user_id(user_id)

            if not preference:
                return None

            return self.update(preference.id, preference_data)

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(
                f"Failed to update family preferences for user {user_id}: {str(e)}"
            )

    def create_or_update(
        self, user_id: int, preference_data: Dict[str, Any]
    ) -> FamilyPreference:
        """
        Create new preferences or update existing ones for a user.

        Args:
            user_id: The user's ID
            preference_data: Dictionary containing preference data

        Returns:
            FamilyPreference instance (created or updated)
        """
        existing_preference = self.get_by_user_id(user_id)

        if existing_preference:
            updated_preference = self.update_by_user_id(user_id, preference_data)
            if updated_preference:
                return updated_preference
            else:
                raise Exception(f"Failed to update preferences for user {user_id}")
        else:
            return self.create(user_id, preference_data)

    def delete_by_user_id(self, user_id: int) -> bool:
        """
        Delete family preferences by user ID.

        Args:
            user_id: The user's ID

        Returns:
            True if deleted, False if not found
        """
        try:
            preference = self.get_by_user_id(user_id)

            if not preference:
                return False

            self.db.delete(preference)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(
                f"Failed to delete family preferences for user {user_id}: {str(e)}"
            )

    def delete(self, preference_id: int) -> bool:
        """
        Delete family preferences by ID.

        Args:
            preference_id: The preference record ID

        Returns:
            True if deleted, False if not found
        """
        try:
            preference = (
                self.db.query(FamilyPreference)
                .filter(FamilyPreference.id == preference_id)
                .first()
            )

            if not preference:
                return False

            self.db.delete(preference)
            self.db.commit()

            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            raise Exception(
                f"Failed to delete family preference {preference_id}: {str(e)}"
            )

    def get_all_by_user_ids(self, user_ids: list[int]) -> list[FamilyPreference]:
        """
        Get family preferences for multiple users.

        Args:
            user_ids: List of user IDs

        Returns:
            List of FamilyPreference instances
        """
        return (
            self.db.query(FamilyPreference)
            .filter(FamilyPreference.user_id.in_(user_ids))
            .all()
        )

    def exists_for_user(self, user_id: int) -> bool:
        """
        Check if family preferences exist for a user.

        Args:
            user_id: The user's ID

        Returns:
            True if preferences exist, False otherwise
        """
        return (
            self.db.query(FamilyPreference)
            .filter(FamilyPreference.user_id == user_id)
            .first()
            is not None
        )
