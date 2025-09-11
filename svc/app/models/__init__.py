from . import relationships
from .activity import Activity
from .activity_suggestion import ActivitySuggestion
from .base import Base
from .family_preference import FamilyPreference
from .kid import Kid
from .user import User
from .user_behavior_analytic import UserBehaviorAnalytic
from .week_activity import WeekActivity

# This ensures all models are imported when the package is imported
__all__ = [
    "Base",
    "User",
    "Kid",
    "Activity",
    "WeekActivity",
    "UserBehaviorAnalytic",
    "ActivitySuggestion",
    "FamilyPreference",
]
