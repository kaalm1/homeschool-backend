from fastapi import APIRouter, status

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

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/preferences", status_code=status.HTTP_200_OK)
async def get_preference_options():
    """Get all available preference options for family settings."""
    return {
        "learning_priorities": LearningPriority.to_frontend(),
        "preferred_time_slots": PreferredTimeSlot.to_frontend(),
        "group_activity_comfort": GroupActivityComfort.to_frontend(),
        "new_experience_openness": NewExperienceOpenness.to_frontend(),
        "available_days": DaysOfWeek.to_frontend(),
    }


@router.get("/all", status_code=status.HTTP_200_OK)
async def get_all_settings():
    """Get all settings options - both activity filters and user preferences."""
    preferences = await get_preference_options()

    return {
        "filters": {
            "costs": Cost.to_frontend(),
            "durations": Duration.to_frontend(),
            "participants": Participants.to_frontend(),
            "locations": Location.to_frontend(),
            "seasons": Season.to_frontend(),
            "age_groups": AgeGroup.to_frontend(),
            "frequency": Frequency.to_frontend(),
            "themes": Theme.to_frontend(),
            "activity_types": ActivityType.to_frontend(),
        },
        "preferences": preferences,
    }
