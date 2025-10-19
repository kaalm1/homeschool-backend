from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.datatypes.enums import ItemStatus, Priority
from svc.app.models.todo_item import TodoItem


class TodoRepository(BaseRepository[TodoItem]):
    """Todo repository with todo-specific operations"""

    def __init__(self, db: Session):
        super().__init__(db, TodoItem)

    def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[TodoItem]:
        """Get all todos for a user"""
        return self.get_many_by_field("user_id", user_id, skip, limit)

    def get_active_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[TodoItem]:
        """Get active (pending) todos for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id, self.model.status == ItemStatus.PENDING
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_completed_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[TodoItem]:
        """Get completed todos for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id, self.model.status == ItemStatus.COMPLETED
            )
            .order_by(self.model.completed_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_priority(
        self, user_id: int, priority: Priority, skip: int = 0, limit: int = 100
    ) -> List[TodoItem]:
        """Get todos by priority for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.priority == priority,
                self.model.status == ItemStatus.PENDING,
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_overdue_by_user(self, user_id: int) -> List[TodoItem]:
        """Get overdue todos for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.status == ItemStatus.PENDING,
                self.model.due_date < datetime.utcnow(),
            )
            .order_by(self.model.due_date)
        )
        return list(self.db.scalars(stmt).all())

    def get_due_soon_by_user(self, user_id: int, hours: int = 24) -> List[TodoItem]:
        """Get todos due within specified hours for a user"""
        from datetime import timedelta

        future_time = datetime.utcnow() + timedelta(hours=hours)

        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.status == ItemStatus.PENDING,
                self.model.due_date.between(datetime.utcnow(), future_time),
            )
            .order_by(self.model.due_date)
        )
        return list(self.db.scalars(stmt).all())

    def create_todo(
        self,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        priority: Optional[Priority] = None,
        due_date: Optional[datetime] = None,
        estimated_hours: Optional[float] = None,
        tags: Optional[str] = None,
    ) -> TodoItem:
        """Create a new todo for a user"""
        return self.create(
            {
                "user_id": user_id,
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date,
                "estimated_hours": estimated_hours,
                "tags": tags,
                "status": ItemStatus.PENDING,
            }
        )

    def mark_complete(self, todo_id: int) -> Optional[TodoItem]:
        """Mark a todo as complete"""
        todo = self.get(todo_id)
        if not todo:
            return None

        todo.mark_complete()
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def mark_deleted(self, todo_id: int) -> Optional[TodoItem]:
        """Soft delete a todo"""
        todo = self.get(todo_id)
        if not todo:
            return None

        todo.mark_deleted()
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def count_by_user(self, user_id: int) -> int:
        """Count total todos for a user"""
        stmt = select(self.model).where(self.model.user_id == user_id)
        return len(list(self.db.scalars(stmt).all()))

    def count_active_by_user(self, user_id: int) -> int:
        """Count active todos for a user"""
        stmt = select(self.model).where(
            self.model.user_id == user_id, self.model.status == ItemStatus.PENDING
        )
        return len(list(self.db.scalars(stmt).all()))
