from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from svc.app.datatypes.enums import ItemStatus, ShoppingCategory
from svc.app.models.base import BaseModel

if TYPE_CHECKING:
    from svc.app.models.user import User

# Define PostgreSQL ENUMs
shopping_status_enum = ENUM(ItemStatus, name="shopping_status_enum", create_type=True)
shopping_category_enum = ENUM(
    ShoppingCategory, name="shopping_category_enum", create_type=True
)


class ShoppingItem(BaseModel):
    """Shopping item model"""

    __tablename__ = "shopping_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    item_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    quantity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    category: Mapped[Optional[ShoppingCategory]] = mapped_column(
        shopping_category_enum, nullable=True, index=True
    )

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[ItemStatus] = mapped_column(
        shopping_status_enum, default=ItemStatus.PENDING, nullable=False, index=True
    )

    estimated_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    price_verified: Mapped[Optional[bool]] = mapped_column(
        Boolean, default=False, nullable=True
    )

    store_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    purchased_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Priority for shopping (some items more urgent than others)
    priority: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)

    # Foreign key to User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="todos")

    def mark_purchased(self) -> None:
        """Mark as purchased"""
        self.status = ItemStatus.COMPLETED
        self.purchased_at = datetime.utcnow()

    def mark_deleted(self) -> None:
        """Mark as deleted"""
        self.status = ItemStatus.DELETED

    def __repr__(self) -> str:
        return f"<ShoppingItem(id={self.id}, item_name='{self.item_name}', status='{self.status.value}')>"
