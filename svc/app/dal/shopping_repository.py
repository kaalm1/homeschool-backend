from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.datatypes.enums import ItemStatus, ShoppingCategory
from svc.app.models.shopping_item import ShoppingItem


class ShoppingRepository(BaseRepository[ShoppingItem]):
    """Shopping repository with shopping-specific operations"""

    def __init__(self, db: Session):
        super().__init__(db, ShoppingItem)

    def get_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ShoppingItem]:
        """Get all shopping items for a user"""
        return self.get_many_by_field("user_id", user_id, skip, limit)

    def get_active_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ShoppingItem]:
        """Get active (pending) shopping items for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id, self.model.status == ItemStatus.PENDING
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_purchased_by_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[ShoppingItem]:
        """Get purchased shopping items for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id, self.model.status == ItemStatus.COMPLETED
            )
            .order_by(self.model.purchased_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_category(
        self, user_id: int, category: ShoppingCategory, skip: int = 0, limit: int = 100
    ) -> List[ShoppingItem]:
        """Get shopping items by category for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.category == category,
                self.model.status == ItemStatus.PENDING,
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_store(
        self, user_id: int, store_name: str, skip: int = 0, limit: int = 100
    ) -> List[ShoppingItem]:
        """Get shopping items by store name for a user"""
        stmt = (
            select(self.model)
            .where(
                self.model.user_id == user_id,
                self.model.store_name == store_name,
                self.model.status == ItemStatus.PENDING,
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def create_shopping_item(
        self,
        user_id: int,
        item_name: str,
        quantity: Optional[str] = None,
        category: Optional[ShoppingCategory] = None,
        notes: Optional[str] = None,
        estimated_price: Optional[float] = None,
        store_name: Optional[str] = None,
        priority: Optional[int] = 0,
    ) -> ShoppingItem:
        """Create a new shopping item for a user"""
        return self.create(
            {
                "user_id": user_id,
                "item_name": item_name,
                "quantity": quantity,
                "category": category,
                "notes": notes,
                "estimated_price": estimated_price,
                "store_name": store_name,
                "priority": priority,
                "status": ItemStatus.PENDING,
            }
        )

    def mark_purchased(
        self, item_id: int, actual_price: Optional[float] = None
    ) -> Optional[ShoppingItem]:
        """Mark a shopping item as purchased"""
        item = self.get(item_id)
        if not item:
            return None

        item.mark_purchased()
        if actual_price is not None:
            item.actual_price = actual_price

        self.db.commit()
        self.db.refresh(item)
        return item

    def mark_deleted(self, item_id: int) -> Optional[ShoppingItem]:
        """Soft delete a shopping item"""
        item = self.get(item_id)
        if not item:
            return None

        item.mark_deleted()
        self.db.commit()
        self.db.refresh(item)
        return item

    def get_total_estimated_cost(self, user_id: int) -> float:
        """Get total estimated cost for active shopping items"""
        items = self.get_active_by_user(user_id)
        return sum(item.estimated_price or 0 for item in items)

    def get_total_actual_cost(self, user_id: int) -> float:
        """Get total actual cost for purchased items"""
        items = self.get_purchased_by_user(user_id)
        return sum(item.actual_price or 0 for item in items)
