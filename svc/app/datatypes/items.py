from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from svc.app.datatypes.calendar import ParsedCalendar
from svc.app.datatypes.shopping import ParsedShopping
from svc.app.datatypes.todo import ParsedTodo


class UserInputRequest(BaseModel):
    """Request for processing user input"""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Raw text input from user"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Buy milk and eggs, finish project by Friday, dentist appointment Tuesday 2pm"
            }
        }


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


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    item_id: Optional[int] = Field(None, description="Affected item ID")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Todo marked as complete",
                "item_id": 123,
            }
        }


class ProcessedItemsResponse(BaseModel):
    """Response for processed items from AI parsing"""

    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Response message")
    summary: Dict[str, int] = Field(..., description="Count summary of created items")
    todos: List[TodoResponse] = Field(
        default_factory=list, description="Created todo items"
    )
    shopping: List[ShoppingResponse] = Field(
        default_factory=list, description="Created shopping items"
    )
    calendar: List[CalendarResponse] = Field(
        default_factory=list, description="Created calendar events"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Items processed and saved successfully",
                "summary": {"todos": 2, "shopping": 3, "calendar": 1},
                "todos": [
                    {
                        "id": 1,
                        "title": "Finish project",
                        "description": None,
                        "status": "pending",
                        "priority": "high",
                        "due_date": "2025-10-25T17:00:00",
                        "created_at": "2025-10-19T10:00:00",
                        "updated_at": "2025-10-19T10:00:00",
                        "completed_at": None,
                        "estimated_hours": None,
                        "tags": None,
                        "is_overdue": False,
                    }
                ],
                "shopping": [
                    {
                        "id": 1,
                        "item_name": "Milk",
                        "quantity": "1 gallon",
                        "category": "groceries",
                        "notes": None,
                        "estimated_price": 4.99,
                        "actual_price": None,
                        "store_name": None,
                        "priority": 0,
                        "status": "pending",
                        "price_verified": False,
                        "created_at": "2025-10-19T10:00:00",
                        "updated_at": "2025-10-19T10:00:00",
                        "purchased_at": None,
                    }
                ],
                "calendar": [
                    {
                        "id": 1,
                        "title": "Dentist appointment",
                        "description": None,
                        "location": None,
                        "start_time": "2025-10-22T14:00:00",
                        "end_time": None,
                        "all_day": False,
                        "reminder_minutes": 30,
                        "url": None,
                        "attendees": None,
                        "is_recurring": False,
                        "recurrence_rule": None,
                        "status": "pending",
                        "created_at": "2025-10-19T10:00:00",
                        "updated_at": "2025-10-19T10:00:00",
                        "is_past": False,
                        "is_upcoming": True,
                    }
                ],
            }
        }


class AllItemsResponse(BaseModel):
    """Response for all items"""

    todos: List[TodoResponse] = Field(
        default_factory=list, description="All todo items"
    )
    shopping: List[ShoppingResponse] = Field(
        default_factory=list, description="All shopping items"
    )
    calendar: List[CalendarResponse] = Field(
        default_factory=list, description="All calendar events"
    )
    summaries: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Summary statistics for each type"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "todos": [
                    {
                        "id": 1,
                        "title": "Finish project",
                        "status": "pending",
                        "priority": "high",
                        "due_date": "2025-10-25T17:00:00",
                        "created_at": "2025-10-19T10:00:00",
                        "updated_at": "2025-10-19T10:00:00",
                        "is_overdue": False,
                    }
                ],
                "shopping": [
                    {
                        "id": 1,
                        "item_name": "Milk",
                        "quantity": "1 gallon",
                        "category": "groceries",
                        "status": "pending",
                        "created_at": "2025-10-19T10:00:00",
                    }
                ],
                "calendar": [
                    {
                        "id": 1,
                        "title": "Dentist appointment",
                        "start_time": "2025-10-22T14:00:00",
                        "status": "pending",
                        "is_upcoming": True,
                    }
                ],
                "summaries": {
                    "todos": {"count": 5, "active": 3, "overdue": 1},
                    "shopping": {"count": 8, "total_cost": 125.50},
                    "calendar": {"count": 3, "upcoming": 2, "today": 1},
                },
            }
        }
