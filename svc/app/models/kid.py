from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity
    from .user import User


class Kid(BaseModel):
    """Kid model."""

    __tablename__ = "kids"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#a7f3d0", nullable=False)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    parent: Mapped["User"] = relationship("User", back_populates="kids")
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="kid", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Kid(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
