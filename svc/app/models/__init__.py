from . import relationships
from .activity import Activity
from .activity_suggestion import ActivitySuggestion
from .base import Base
from .calendar_event import CalendarEvent
from .family_preference import FamilyPreference
from .kid import Kid
from .shopping_item import ShoppingItem
from .todo_item import TodoItem
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
    "TodoItem",
    "ShoppingItem",
    "CalendarEvent",
]
