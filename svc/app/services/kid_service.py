from typing import List

from ..dal.kid_repository import KidRepository
from ..datatypes.kid import KidCreate, KidResponse, KidUpdate
from ..models.kid import Kid
from ..utils.exceptions import NotFoundError, ValidationError


class KidService:
    """Kid service for handling kid operations."""

    def __init__(self, kid_repository: KidRepository):
        self.kid_repo = kid_repository

    def get_kids_by_parent(self, parent_id: int) -> List[KidResponse]:
        """Get all kids for a parent."""
        kids = self.kid_repo.get_by_parent_id(parent_id)
        return [KidResponse.model_validate(kid) for kid in kids]

    def get_kid_by_id(self, kid_id: int, parent_id: int) -> KidResponse:
        """Get kid by ID, ensuring it belongs to the parent."""
        kid = self.kid_repo.get_kid_by_parent(kid_id, parent_id)
        if not kid:
            raise NotFoundError("Kid not found")
        return KidResponse.model_validate(kid)

    def create_kid(self, kid_data: KidCreate, parent_id: int) -> KidResponse:
        """Create a new kid."""
        kid = self.kid_repo.create_kid(
            name=kid_data.name, color=kid_data.color, parent_id=parent_id
        )
        return KidResponse.model_validate(kid)

    def update_kid(
        self, kid_id: int, kid_data: KidUpdate, parent_id: int
    ) -> KidResponse:
        """Update kid information."""
        # Ensure kid belongs to parent
        existing_kid = self.kid_repo.get_kid_by_parent(kid_id, parent_id)
        if not existing_kid:
            raise NotFoundError("Kid not found")

        update_dict = kid_data.model_dump(exclude_unset=True)
        updated_kid = self.kid_repo.update(kid_id, update_dict)

        return KidResponse.model_validate(updated_kid)

    def delete_kid(self, kid_id: int, parent_id: int) -> bool:
        """Delete a kid."""
        # Ensure kid belongs to parent
        existing_kid = self.kid_repo.get_kid_by_parent(kid_id, parent_id)
        if not existing_kid:
            raise NotFoundError("Kid not found")

        return self.kid_repo.delete(kid_id)
