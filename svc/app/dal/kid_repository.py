from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.models.kid import Kid


class KidRepository(BaseRepository[Kid]):
    """Kid repository with kid-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db, Kid)

    def get_by_parent_id(self, parent_id: int) -> List[Kid]:
        """Get all kids for a parent."""
        return (
            self.db.execute(select(Kid).where(Kid.parent_id == parent_id))
            .scalars()
            .all()
        )

    def create_kid(self, name: str, color: str, dob: str, parent_id: int) -> Kid:
        """Create a new kid."""
        return self.create({"name": name, "color": color, "dob": dob, "parent_id": parent_id})

    def get_kid_by_parent(self, kid_id: int, parent_id: int) -> Kid:
        """Get kid by ID and parent ID for security."""
        return self.db.execute(
            select(Kid).where(Kid.id == kid_id, Kid.parent_id == parent_id)
        ).scalar_one_or_none()
