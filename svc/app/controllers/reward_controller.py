from typing import Annotated, List

from fastapi import APIRouter, Depends, status

from svc.app.datatypes.activity import RewardSummary
from svc.app.dependencies import CurrentUser, get_activity_service
from svc.app.services.activity_service import ActivityService

router = APIRouter(tags=["rewards"])


@router.get(
    "/summary", response_model=List[RewardSummary], status_code=status.HTTP_200_OK
)
async def get_reward_summary(
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Get reward summary showing stars earned by each kid."""
    return activity_service.get_reward_summary(current_user.id)
