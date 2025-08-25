from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, func

from ..database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common CRUD operations."""

    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get(self, id: Any) -> Optional[ModelType]:
        """Get a single record by ID."""
        return self.db.get(self.model, id)

    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a single record by field value."""
        return self.db.execute(
            select(self.model).where(getattr(self.model, field) == value)
        ).scalar_one_or_none()

    def get_all(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with pagination and filtering."""
        query = select(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        return self.db.execute(query.offset(skip).limit(limit)).scalars().all()

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = select(func.count()).select_from(self.model)

        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)

        return self.db.execute(query).scalar() or 0

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[ModelType]:
        """Update an existing record."""
        # Remove None values to avoid updating fields to None
        update_data = {k: v for k, v in obj_in.items() if v is not None}

        if not update_data:
            return self.get(id)

        self.db.execute(
            update(self.model).where(self.model.id == id).values(**update_data)
        )
        self.db.commit()
        return self.get(id)

    def delete(self, id: Any) -> bool:
        """Delete a record by ID."""
        result = self.db.execute(delete(self.model).where(self.model.id == id))
        self.db.commit()
        return result.rowcount > 0

    def exists(self, id: Any) -> bool:
        """Check if a record exists by ID."""
        return self.get(id) is not None
