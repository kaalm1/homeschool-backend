from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from svc.app.dal.base_repository import BaseRepository
from svc.app.models.user import User


class UserRepository(BaseRepository[User]):
    """User repository with user-specific operations."""

    def __init__(self, db: Session):
        super().__init__(db, User)

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return self.get_by_field("email", email)

    def create_user(self, email: str, password_hash: str) -> User:
        """Create a new user."""
        return self.create(
            {"email": email, "password_hash": password_hash, "is_active": True}
        )

    def update_password(self, user_id: int, password_hash: str) -> Optional[User]:
        """Update user password."""
        return self.update(user_id, {"password_hash": password_hash})

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        return self.update(user_id, {"is_active": False})

    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        return self.update(user_id, {"is_active": True})

    def update_family_profile(self, user_id: int, profile_data: dict) -> User:
        user = self.get(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        for key, value in profile_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.family_profile_updated_at = datetime.utcnow()
        self.db.commit()
        return user

    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        return self.get_by_field("google_id", google_id)

    def create_google_user(
        self, email: str, google_id: str, avatar_url: Optional[str] = None
    ) -> User:
        """Create a new user from Google OAuth."""
        return self.create(
            {
                "email": email,
                "google_id": google_id,
                "google_avatar_url": avatar_url,
                "is_active": True,
                "password_hash": None,  # No password for OAuth users
            }
        )

    def link_google_account(
        self, user_id: int, google_id: str, avatar_url: Optional[str] = None
    ) -> User:
        """Link Google account to existing user."""
        update_data = {"google_id": google_id, "google_avatar_url": avatar_url}
        return self.update(user_id, update_data)
