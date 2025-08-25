import secrets
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import bcrypt

from ..config import get_settings


def generate_secret_key(length: int = 32) -> str:
    """Generate a secure random secret key."""
    return secrets.token_urlsafe(length)


def create_jwt_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[dict] = None,
) -> str:
    """Create JWT token with optional expiration and extra claims."""
    settings = get_settings()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )

    to_encode = {"exp": expire, "iat": datetime.now(timezone.utc), "sub": str(subject)}

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")


def verify_jwt_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return bcrypt.verify(plain_password, hashed_password)
