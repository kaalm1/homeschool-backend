from typing import Annotated

from fastapi import APIRouter, Depends, status

from svc.app.datatypes.settings import (
    AllSettingsResponse,
    FilterOptionsResponse,
    PreferenceOptionsResponse,
)
from svc.app.dependencies import CurrentUser, get_current_user, get_settings_service
from svc.app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get(
    "/preferences",
    response_model=PreferenceOptionsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_preference_options(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
):
    """Get all available preference options for family settings."""
    return settings_service.get_preference_options()


@router.get(
    "/filters", response_model=FilterOptionsResponse, status_code=status.HTTP_200_OK
)
async def get_filters_options(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
):
    """Get all available filter options for activities."""
    return settings_service.get_filter_options()


@router.get("/all", response_model=AllSettingsResponse, status_code=status.HTTP_200_OK)
async def get_all_settings(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    settings_service: Annotated[SettingsService, Depends(get_settings_service)],
):
    """Get all settings options - both activity filters and user preferences."""
    return settings_service.get_all_settings()
