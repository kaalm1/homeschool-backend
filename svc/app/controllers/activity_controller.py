from typing import Annotated, List

from fastapi import APIRouter, Depends, Query, status

from svc.app.datatypes.activity import (ActivityCreate, ActivityResponse,
                                        ActivityUpdate)
from svc.app.datatypes.enums import (ActivityType, AgeGroup, Cost, Duration,
                                     Frequency, Location, Participants, Season,
                                     Theme)
from svc.app.dependencies import (CurrentUser, get_activity_service,
                                  get_current_user)
from svc.app.services.activity_service import ActivityService

router = APIRouter(tags=["activities"])


@router.get("/filters", status_code=status.HTTP_200_OK)
async def get_activity_filters():
    """Get all available filter options for activities."""
    return {
        "costs": Cost.to_frontend(),
        "durations": Duration.to_frontend(),
        "participants": Participants.to_frontend(),
        "locations": Location.to_frontend(),
        "seasons": Season.to_frontend(),
        "age_groups": AgeGroup.to_frontend(),
        "frequency": Frequency.to_frontend(),
        "themes": Theme.to_frontend(),
        "activity_types": ActivityType.to_frontend(),
    }


@router.get("", response_model=List[ActivityResponse], status_code=status.HTTP_200_OK)
async def get_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    kid_id: int = Query(None, description="Filter by kid ID"),
):
    """Get activities for the current user. Optionally filter by kid."""
    if kid_id:
        return activity_service.get_activities_by_kid(kid_id, current_user.id)
    return activity_service.get_activities_by_parent(current_user.id)


@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED)
async def create_activity(
    activity_data: ActivityCreate,
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Create a new activity."""
    return activity_service.create_activity(activity_data, current_user.id)


@router.get(
    "/{activity_id}", response_model=ActivityResponse, status_code=status.HTTP_200_OK
)
async def get_activity(
    activity_id: int,
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Get a specific activity by ID."""
    # This will validate ownership through the service
    activities = activity_service.get_activities_by_parent(current_user.id)
    for activity in activities:
        if activity.id == activity_id:
            return activity
    from ..utils.exceptions import NotFoundError

    raise NotFoundError("Activity not found")


@router.patch(
    "/{activity_id}", response_model=ActivityResponse, status_code=status.HTTP_200_OK
)
async def update_activity(
    activity_id: int,
    activity_data: ActivityUpdate,
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Update an activity."""
    return activity_service.update_activity(activity_id, activity_data, current_user.id)


@router.post(
    "/{activity_id}/toggle",
    response_model=ActivityResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_activity(
    activity_id: int,
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Toggle activity completion status."""
    return activity_service.toggle_activity(activity_id, current_user.id)


@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_activity(
    activity_id: int,
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Delete an activity."""
    activity_service.delete_activity(activity_id, current_user.id)
    return None
