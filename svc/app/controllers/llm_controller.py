import logging
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException

from svc.app.dependencies import CurrentUser
from svc.app.llm.schemas.tagging_schemas import (ActivityTaggingRequest,
                                                 ActivityTaggingResponse,
                                                 TaggedActivity)
from svc.app.llm.services.tagging_service import activity_tagging_service
from svc.app.services.activity_service import ActivityService
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/tag-activities", response_model=ActivityTaggingResponse)
async def tag_activities(
    current_user: CurrentUser,
    request: ActivityTaggingRequest,
    activity_service: ActivityService = Depends(),
):
    """Tag activities using LLM"""
    try:
        # Get enum values from your existing models/services
        enums = activity_service.get_llm_enum_values()

        tagged_activities: List[TaggedActivity] = (
            await activity_tagging_service.tag_activities(request.activities, enums)
        )

        # TODO: Need to take these tagged activities and save it to the user
        # TODO: For now kids will be manual, this works only on a family level

        return ActivityTaggingResponse(
            tagged_activities=tagged_activities, total_count=len(tagged_activities)
        )

    except LLMProcessingError as e:
        logger.error(f"LLM processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in tag_activities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
