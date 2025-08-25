from typing import List, Annotated
from fastapi import APIRouter, Depends, status

from ..services.activity_service import ActivityService
from ..datatypes.activity import RewardSummary
from ..dependencies import get_activity_service, CurrentUser

router = APIRouter()


@router.get(
    "/summary", response_model=List[RewardSummary], status_code=status.HTTP_200_OK
)
async def get_reward_summary(
    current_user: CurrentUser,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Get reward summary showing stars earned by each kid."""
    return activity_service.get_reward_summary(current_user.id)
