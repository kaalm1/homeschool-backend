from typing import Optional

from svc.app.dal.user_repository import UserRepository
from svc.app.datatypes.user import UserResponse, UserUpdate
from svc.app.models.user import User
from svc.app.utils.exceptions import NotFoundError


class UserService:
    """User service for handling user operations."""

    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def get_user_profile(self, user_id: int) -> UserResponse:
        """Get user profile information."""
        user = self.get_user_by_id(user_id)
        return UserResponse.model_validate(user)

    def update_user(self, user_id: int, update_data: UserUpdate) -> UserResponse:
        """Update user information."""
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_user = self.user_repo.update(user_id, update_dict)

        return UserResponse.model_validate(updated_user)

    def deactivate_user(self, user_id: int) -> UserResponse:
        """Deactivate user account."""
        user = self.user_repo.deactivate_user(user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserResponse.model_validate(user)
