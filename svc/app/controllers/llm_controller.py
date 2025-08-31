import logging

from fastapi import APIRouter, Depends, HTTPException

from svc.app.llm.schemas.tagging_schemas import (ActivityTaggingRequest,
                                                 ActivityTaggingResponse)
from svc.app.llm.services.tagging_service import activity_tagging_service
from svc.app.services.activity_service import ActivityService
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/tag-activities", response_model=ActivityTaggingResponse)
async def tag_activities(
    request: ActivityTaggingRequest, activity_service: ActivityService = Depends()
):
    """Tag activities using LLM"""
    try:
        # Get enum values from your existing models/services
        enums = activity_service.get_enum_values()

        tagged_activities = await activity_tagging_service.tag_activities(
            request.activities, enums
        )

        return ActivityTaggingResponse(
            tagged_activities=tagged_activities, total_count=len(tagged_activities)
        )

    except LLMProcessingError as e:
        logger.error(f"LLM processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in tag_activities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
