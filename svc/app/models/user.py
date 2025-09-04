from typing import TYPE_CHECKING, List, Optional
from datetime import datetime

from sqlalchemy import String, Float, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .activity import Activity
    from .kid import Kid
    from .week_activity import WeekActivity


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # Nullable for OAuth users
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Google OAuth fields
    google_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    google_avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Location fields - flexible approach for LLM processing
    # Store full address as single field for easy LLM parsing
    address: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Full address string

    # Separate components for structured queries if needed
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zip_code: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )
    country: Mapped[str] = mapped_column(String(50), nullable=False, default="US")

    # Precise coordinates for distance calculations
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Location metadata
    location_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    location_accuracy: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # GPS accuracy in meters

    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    kids: Mapped[List["Kid"]] = relationship(
        "Kid", back_populates="parent", cascade="all, delete-orphan"
    )

    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def display_name(self) -> str:
        """Get user's display name (email username for now)."""
        return self.email.split("@")[0]

    @property
    def has_location(self) -> bool:
        """Check if user has location data."""
        return bool(self.latitude and self.longitude)

    @property
    def location_for_llm(self) -> Optional[str]:
        """Get location string optimized for LLM processing."""
        if self.address:
            return self.address

        # Fallback to structured components
        parts = []
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)

        return ", ".join(parts) if parts else None

    def update_location(
        self,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        accuracy: Optional[float] = None,
    ) -> None:
        """Update user location with timestamp."""
        if address:
            self.address = address
        if city:
            self.city = city
        if state:
            self.state = state
        if zip_code:
            self.zip_code = zip_code
        if latitude is not None and longitude is not None:
            self.latitude = latitude
            self.longitude = longitude
        if accuracy:
            self.location_accuracy = accuracy

        self.location_updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', has_location={self.has_location})>"
