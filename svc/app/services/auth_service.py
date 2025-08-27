from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.hash import bcrypt

from ..config import get_settings
from ..dal.user_repository import UserRepository
from ..datatypes.auth import LoginRequest, RegisterRequest, TokenResponse
from ..models.user import User
from ..utils.exceptions import AuthenticationError, ValidationError

security = HTTPBearer(auto_error=False)


class AuthService:
    """Authentication service for handling user auth operations."""

    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository
        self.settings = get_settings()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.user_repo.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not self._verify_password(password, user.password_hash):
            return None
        return user

    def create_access_token(self, user: User) -> TokenResponse:
        """Create JWT access token for user."""
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        expire = datetime.now(timezone.utc) + expires_delta

        to_encode = {
            "sub": user.email,
            "user_id": user.id,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        encoded_jwt = jwt.encode(to_encode, self.settings.secret_key, algorithm="HS256")

        return TokenResponse(
            access_token=encoded_jwt,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    def login(self, login_data: LoginRequest) -> TokenResponse:
        """Login user and return access token."""
        user = self.authenticate_user(login_data.email, login_data.password)
        if not user:
            raise AuthenticationError("Invalid email or password")

        return self.create_access_token(user)

    def register(self, register_data: RegisterRequest) -> TokenResponse:
        """Register new user and return access token."""
        # Check if user already exists
        existing_user = self.user_repo.get_by_email(register_data.email)
        if existing_user:
            raise ValidationError("Email already registered")

        # Create new user
        password_hash = self._hash_password(register_data.password)
        user = self.user_repo.create_user(
            email=register_data.email, password_hash=password_hash
        )

        return self.create_access_token(user)

    # def get_current_user(
    #     self, credentials: HTTPAuthorizationCredentials = Depends(security)
    # ) -> User:
    #     """Get current authenticated user from JWT token."""
    #     if not credentials:
    #         raise AuthenticationError("Authentication required")
    #
    #     try:
    #         payload = jwt.decode(
    #             credentials.credentials, self.settings.secret_key, algorithms=["HS256"]
    #         )
    #         email: str = payload.get("sub")
    #         user_id: int = payload.get("user_id")
    #
    #         if email is None or user_id is None:
    #             raise AuthenticationError("Invalid token payload")
    #
    #     except JWTError:
    #         raise AuthenticationError("Invalid token")
    #
    #     user = self.user_repo.get(user_id)
    #     if not user or not user.is_active:
    #         raise AuthenticationError("User not found or inactive")
    #
    #     return user

    def get_current_user_from_token(
        self, credentials: HTTPAuthorizationCredentials
    ) -> User:
        """Decode JWT and return user."""
        if not credentials:
            raise AuthenticationError("Authentication required")

        try:
            payload = jwt.decode(
                credentials.credentials,
                self.settings.secret_key,
                algorithms=["HS256"],
            )
            email: str = payload.get("sub")
            user_id: int = payload.get("user_id")

            if email is None or user_id is None:
                raise AuthenticationError("Invalid token payload")
        except JWTError:
            raise AuthenticationError("Invalid token")

        user = self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        return user

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return bcrypt.verify(plain_password, hashed_password)
