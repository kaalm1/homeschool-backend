from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from svc.app.datatypes.calendar import ParsedCalendar
from svc.app.datatypes.shopping import ParsedShopping
from svc.app.datatypes.todo import ParsedTodo


class ParsedResult(BaseModel):
    """Container for all parsed items"""

    todos: List[ParsedTodo] = Field(
        default_factory=list, description="List of parsed todo items"
    )
    shopping: List[ParsedShopping] = Field(
        default_factory=list, description="List of parsed shopping items"
    )
    calendar: List[ParsedCalendar] = Field(
        default_factory=list, description="List of parsed calendar events"
    )

    @property
    def total_items(self) -> int:
        """Total number of parsed items"""
        return len(self.todos) + len(self.shopping) + len(self.calendar)

    @property
    def has_items(self) -> bool:
        """Check if any items were parsed"""
        return self.total_items > 0

    @property
    def summary(self) -> dict:
        """Get summary of parsed items"""
        return {
            "todos": len(self.todos),
            "shopping": len(self.shopping),
            "calendar": len(self.calendar),
            "total": self.total_items,
        }
