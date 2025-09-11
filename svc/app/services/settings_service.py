from svc.app.datatypes.enums import (
    ActivityType,
    AgeGroup,
    Cost,
    DaysOfWeek,
    Duration,
    Frequency,
    GroupActivityComfort,
    LearningPriority,
    Location,
    NewExperienceOpenness,
    Participants,
    PreferredTimeSlot,
    Season,
    Theme,
)
from svc.app.datatypes.settings import (
    AllSettingsResponse,
    FilterOptionsResponse,
    PreferenceOptionsResponse,
)


class SettingsService:
    """Service for managing settings and configuration options."""

    def get_preference_options(self) -> PreferenceOptionsResponse:
        """Get all available preference options for family settings."""
        return PreferenceOptionsResponse(
            learning_priorities=LearningPriority.to_frontend(),
            preferred_time_slots=PreferredTimeSlot.to_frontend(),
            group_activity_comfort=GroupActivityComfort.to_frontend(),
            new_experience_openness=NewExperienceOpenness.to_frontend(),
            available_days=DaysOfWeek.to_frontend(),
        )

    def get_filter_options(self) -> FilterOptionsResponse:
        """Get all available filter options for activities."""
        return FilterOptionsResponse(
            costs=Cost.to_frontend(),
            durations=Duration.to_frontend(),
            participants=Participants.to_frontend(),
            locations=Location.to_frontend(),
            seasons=Season.to_frontend(),
            age_groups=AgeGroup.to_frontend(),
            frequency=Frequency.to_frontend(),
            themes=Theme.to_frontend(),
            activity_types=ActivityType.to_frontend(),
        )

    def get_all_settings(self) -> AllSettingsResponse:
        """Get all settings options - both activity filters and user preferences."""
        return AllSettingsResponse(
            filters=self.get_filter_options(),
            preferences=self.get_preference_options(),
        )
