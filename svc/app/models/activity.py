from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .kid import Kid


class Activity(BaseModel):
    """Activity model."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), default="General", nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    kid_id: Mapped[int] = mapped_column(
        ForeignKey("kids.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Relationships
    kid: Mapped["Kid"] = relationship("Kid", back_populates="activities")

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, title='{self.title}', kid_id={self.kid_id})>"
