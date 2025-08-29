# svc/app/llm/enum_loader.py
"""Enum loader for LLM services - loads at startup and caches values."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from svc.app.datatypes.enums import (AGEGROUP_TO_AI, COST_TO_AI,
                                     DURATION_TO_AI, LOCATION_TO_AI,
                                     PARTICIPANTS_TO_AI, SEASON_TO_AI,
                                     AgeGroup, Cost, Duration, Location,
                                     Participants, Season)
from svc.app.models.activity_type import ActivityType
from svc.app.models.theme import Theme

logger = logging.getLogger(__name__)


class EnumCache:
    """Singleton cache for enum values loaded at startup."""

    _instance: Optional["EnumCache"] = None
    _initialized: bool = False

    def __new__(cls) -> "EnumCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._enum_values: Dict[str, Any] = {}
            self._themes: List[str] = []
            self._activity_types: List[str] = []
            EnumCache._initialized = True

    def initialize(self, db_session: Session) -> None:
        """Initialize the cache with database values."""
        try:
            logger.info("Loading enum values at startup...")

            # Load themes from database
            themes = db_session.query(Theme).all()
            self._themes = [theme.name for theme in themes]
            logger.info(f"Loaded {len(self._themes)} themes")

            # Load activity types from database
            activity_types = db_session.query(ActivityType).all()
            self._activity_types = [at.name for at in activity_types]
            logger.info(f"Loaded {len(self._activity_types)} activity types")

            # Build the complete enum values dict
            self._enum_values = {
                # Enum values with AI-friendly descriptions
                "cost": list(COST_TO_AI.values()),
                "duration": list(DURATION_TO_AI.values()),
                "participant": list(PARTICIPANTS_TO_AI.values()),
                "age_group": list(AGEGROUP_TO_AI.values()),
                "location": list(LOCATION_TO_AI.values()),
                "season": list(SEASON_TO_AI.values()),
                # Database values (cached at startup)
                "themes": self._themes.copy(),
                "activity_types": self._activity_types.copy(),
            }

            logger.info("Enum cache initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize enum cache: {e}")
            # Fallback to just enum values
            self._enum_values = {
                "cost": list(COST_TO_AI.values()),
                "duration": list(DURATION_TO_AI.values()),
                "participant": list(PARTICIPANTS_TO_AI.values()),
                "age_group": list(AGEGROUP_TO_AI.values()),
                "location": list(LOCATION_TO_AI.values()),
                "season": list(SEASON_TO_AI.values()),
                "themes": [],
                "activity_types": [],
            }

    def get_enum_values(self) -> Dict[str, Any]:
        """Get cached enum values."""
        if not self._enum_values:
            logger.warning("Enum cache not initialized, returning empty dict")
            return {}
        return self._enum_values.copy()

    def get_themes(self) -> List[str]:
        """Get cached theme names."""
        return self._themes.copy()

    def get_activity_types(self) -> List[str]:
        """Get cached activity type names."""
        return self._activity_types.copy()

    def refresh_themes(self, db_session: Session) -> None:
        """Refresh themes from database (call when themes are added/removed)."""
        themes = db_session.query(Theme).all()
        self._themes = [theme.name for theme in themes]
        self._enum_values["themes"] = self._themes.copy()
        logger.info(f"Refreshed themes cache: {len(self._themes)} themes")

    def refresh_activity_types(self, db_session: Session) -> None:
        """Refresh activity types from database (call when types are added/removed)."""
        activity_types = db_session.query(ActivityType).all()
        self._activity_types = [at.name for at in activity_types]
        self._enum_values["activity_types"] = self._activity_types.copy()
        logger.info(
            f"Refreshed activity types cache: {len(self._activity_types)} activity types"
        )


# Global instance
enum_cache = EnumCache()
