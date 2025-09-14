from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from svc.app.models.activity import Activity
    from svc.app.models.activity_suggestion import ActivitySuggestion
    from svc.app.models.family_preference import FamilyPreference
    from svc.app.models.kid import Kid
    from svc.app.models.user_behavior_analytic import UserBehaviorAnalytic


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

    # Core Family Demographics (stable, essential)
    family_size: Mapped[Optional[int]] = mapped_column(nullable=True, default=1)
    adults_count: Mapped[Optional[int]] = mapped_column(nullable=True, default=1)

    # Transportation & Mobility (fairly stable)
    has_car: Mapped[bool] = mapped_column(default=True, nullable=False)
    max_travel_distance: Mapped[Optional[int]] = mapped_column(
        nullable=True, default=30
    )  # miles

    # Basic Budget Info (changes occasionally)
    weekly_activity_budget: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )

    # Activity Scheduling (changes seasonally)
    max_activities_per_week: Mapped[int] = mapped_column(default=5, nullable=False)

    # Timestamps for cache invalidation
    family_profile_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    premium_subscription: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    premium_subscription_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    premium_subscription_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    premium_subscription_tier: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )
    premium_subscription_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, default=0, nullable=True
    )

    # Relationships
    kids: Mapped[List["Kid"]] = relationship(
        "Kid", back_populates="parent", cascade="all, delete-orphan"
    )

    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="user", cascade="all, delete-orphan"
    )

    family_preferences: Mapped[Optional["FamilyPreference"]] = relationship(
        "FamilyPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    behavior_analytics: Mapped[Optional["UserBehaviorAnalytic"]] = relationship(
        "UserBehaviorAnalytic",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    activity_suggestions: Mapped[List["ActivitySuggestion"]] = relationship(
        "ActivitySuggestion", back_populates="user", cascade="all, delete-orphan"
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
    def needs_kids_info(self) -> bool:
        """Check if family has kids but no Kid records."""
        return self.family_size > self.adults_count and len(self.kids) == 0

    @property
    def has_complete_profile(self) -> bool:
        """Check if user has minimum required info for recommendations."""
        return bool(
            self.has_location
            and self.family_size
            and (len(self.kids) > 0 or self.family_size == self.adults_count)
        )

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
