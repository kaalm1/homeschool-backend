from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from svc.app.datatypes.common import TimestampMixin
from svc.app.datatypes.enums import ItemStatus, Priority


class TodoBase(BaseModel):
    """Base todo schema"""

    title: str = Field(..., min_length=1, max_length=255, description="Todo title")
    description: Optional[str] = Field(None, description="Todo description")
    priority: Optional[Priority] = Field(None, description="Priority level")
    due_date: Optional[datetime] = Field(None, description="Due date")
    estimated_hours: Optional[float] = Field(
        None, ge=0, description="Estimated hours to complete"
    )
    tags: Optional[str] = Field(
        None, max_length=500, description="Comma-separated tags"
    )


class TodoCreate(TodoBase):
    """Schema for creating todos"""

    pass


class TodoUpdate(BaseModel):
    """Schema for updating todos"""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[float] = Field(None, ge=0)
    tags: Optional[str] = Field(None, max_length=500)
    status: Optional[ItemStatus] = None


class TodoResponse(TodoBase, TimestampMixin):
    """Schema for todo responses"""

    id: int = Field(..., description="Todo ID")
    status: ItemStatus = Field(..., description="Todo status")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    is_overdue: bool = Field(..., description="Whether todo is overdue")

    class Config:
        from_attributes = True


class ParsedTodo(BaseModel):
    """Parsed todo from AI"""

    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    tags: Optional[str] = None


class TodoSummary(BaseModel):
    """Summary statistics for todos"""

    total: int = Field(..., description="Total todos")
    pending: int = Field(..., description="Pending todos")
    completed: int = Field(..., description="Completed todos")
    overdue: int = Field(..., description="Overdue todos")
