from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from svc.app.datatypes.family_preference import (
    FamilyPreferenceResponse,
    FamilyPreferenceUpdateRequest,
)
from svc.app.dependencies import get_current_user, get_family_preference_service
from svc.app.models.user import User
from svc.app.services.family_preference_service import FamilyPreferenceService

router = APIRouter(prefix="/api/v1/family", tags=["Family Preferences"])


@router.get("/preferences", response_model=FamilyPreferenceResponse)
def get_family_preferences(
    current_user: User = Depends(get_current_user),
    service: FamilyPreferenceService = Depends(get_family_preference_service),
) -> FamilyPreferenceResponse:
    """
    Get current user's family preferences.

    Returns all family preferences for the authenticated user,
    including default values if no preferences are set.
    """
    try:
        preferences = service.get_family_preferences(current_user.id)
        return FamilyPreferenceResponse(**preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve family preferences: {str(e)}",
        )


@router.put("/preferences", response_model=FamilyPreferenceResponse)
def update_family_preferences(
    request: FamilyPreferenceUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: FamilyPreferenceService = Depends(get_family_preference_service),
) -> FamilyPreferenceResponse:
    """
    Update family preferences for the current user.

    Updates the user's family preferences with the provided data.
    Creates new preferences if none exist, otherwise updates existing ones.
    """
    try:
        updated_preferences = service.update_family_preferences(
            current_user.id, request.dict(exclude_unset=True)
        )
        return FamilyPreferenceResponse(**updated_preferences)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update family preferences: {str(e)}",
        )


@router.patch("/preferences", response_model=FamilyPreferenceResponse)
def partial_update_family_preferences(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    service: FamilyPreferenceService = Depends(get_family_preference_service),
) -> FamilyPreferenceResponse:
    """
    Partially update family preferences for the current user.

    Updates only the provided fields, leaving others unchanged.
    """
    try:
        updated_preferences = service.partial_update_family_preferences(
            current_user.id, request
        )
        return FamilyPreferenceResponse(**updated_preferences)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update family preferences: {str(e)}",
        )


@router.delete("/preferences")
def reset_family_preferences(
    current_user: User = Depends(get_current_user),
    service: FamilyPreferenceService = Depends(get_family_preference_service),
) -> Dict[str, str]:
    """
    Reset family preferences to defaults.

    Deletes all custom preferences for the user, effectively resetting to defaults.
    """
    try:
        service.reset_family_preferences(current_user.id)
        return {"message": "Family preferences reset to defaults successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset family preferences: {str(e)}",
        )
