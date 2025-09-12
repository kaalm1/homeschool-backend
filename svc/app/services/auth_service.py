from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from jose import JWTError, jwt
from passlib.hash import bcrypt

from svc.app.config import get_settings
from svc.app.dal.user_repository import UserRepository
from svc.app.datatypes.auth import (
    GoogleAuthRequest,
    GoogleUserInfo,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)
from svc.app.models.user import User
from svc.app.utils.exceptions import AuthenticationError, ValidationError

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

    def get_google_auth_url(self) -> str:
        """Generate Google OAuth authorization URL."""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.settings.google_redirect_uri],
                }
            },
            scopes=["openid", "email", "profile"],
        )
        flow.redirect_uri = self.settings.google_redirect_uri

        authorization_url, state = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )

        return authorization_url

    def verify_google_token(self, token: str) -> GoogleUserInfo:
        """Verify Google ID token and extract user info."""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), self.settings.google_client_id
            )

            return GoogleUserInfo(
                id=idinfo["sub"],
                email=idinfo["email"],
                name=idinfo.get("name", ""),
                picture=idinfo.get("picture"),
            )
        except ValueError as e:
            raise AuthenticationError(f"Invalid Google token: {str(e)}")

    def handle_google_callback(self, auth_request: GoogleAuthRequest) -> TokenResponse:
        """Handle Google OAuth callback and create/login user."""
        try:
            # Exchange authorization code for tokens
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.settings.google_client_id,
                        "client_secret": self.settings.google_client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [self.settings.google_redirect_uri],
                    }
                },
                scopes=["openid", "email", "profile"],
            )
            flow.redirect_uri = self.settings.google_redirect_uri

            # Fetch token
            flow.fetch_token(code=auth_request.code)

            # Get user info from ID token
            credentials = flow.credentials
            google_user = self.verify_google_token(credentials.id_token)

            # Check if user exists
            user = self.user_repo.get_by_google_id(google_user.id)

            if not user:
                # Check if user exists by email (for account linking)
                existing_user = self.user_repo.get_by_email(google_user.email)

                if existing_user:
                    # Link Google account to existing user
                    user = self.user_repo.link_google_account(
                        user_id=existing_user.id,
                        google_id=google_user.id,
                        avatar_url=google_user.picture,
                    )
                else:
                    # Create new user
                    user = self.user_repo.create_google_user(
                        email=google_user.email,
                        google_id=google_user.id,
                        avatar_url=google_user.picture,
                    )

            if not user.is_active:
                raise AuthenticationError("Account is deactivated")

            return self.create_access_token(user)

        except Exception as e:
            raise AuthenticationError(f"Google authentication failed: {str(e)}")
