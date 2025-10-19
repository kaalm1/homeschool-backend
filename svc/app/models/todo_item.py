from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import ItemStatus, Priority

from .base import BaseModel

# Define PostgreSQL ENUMs
item_status_enum = ENUM(ItemStatus, name="item_status_enum", create_type=True)
priority_enum = ENUM(Priority, name="priority_enum", create_type=True)

if TYPE_CHECKING:
    from svc.app.models.user import User


class TodoItem(BaseModel):
    """Todo item model"""

    __tablename__ = "todo_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[ItemStatus] = mapped_column(
        item_status_enum, default=ItemStatus.PENDING, nullable=False, index=True
    )

    priority: Mapped[Optional[Priority]] = mapped_column(priority_enum, nullable=True)

    due_date: Mapped[Optional[datetime]] = mapped_column(nullable=True, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Additional metadata
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Foreign key to User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="todos")

    def mark_complete(self) -> None:
        """Mark as completed"""
        self.status = ItemStatus.COMPLETED
        self.completed_at = datetime.utcnow()

    def mark_deleted(self) -> None:
        """Mark as deleted"""
        self.status = ItemStatus.DELETED

    @property
    def is_overdue(self) -> bool:
        """Check if todo is overdue"""
        if self.due_date and self.status == ItemStatus.PENDING:
            return datetime.utcnow() > self.due_date
        return False

    def __repr__(self) -> str:
        return f"<TodoItem(id={self.id}, title='{self.title}', status='{self.status.value}')>"
