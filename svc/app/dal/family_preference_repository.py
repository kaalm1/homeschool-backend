from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.models.family_preference import FamilyPreferences


class FamilyPreferencesRepository(BaseRepository):
    def __init__(self, db: Session):
        super().__init__(db, FamilyPreferences)

    def get_by_user(self, user_id: int) -> Optional[FamilyPreferences]:
        return (
            self.db.query(FamilyPreferences)
            .filter(FamilyPreferences.user_id == user_id)
            .first()
        )

    def create_or_update(
        self, user_id: int, preferences_data: dict
    ) -> FamilyPreferences:
        preferences = self.get_by_user(user_id)
        if preferences:
            for key, value in preferences_data.items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
            preferences.updated_at = datetime.utcnow()
        else:
            preferences = FamilyPreferences(user_id=user_id, **preferences_data)
            self.db.add(preferences)

        self.db.commit()
        return preferences
