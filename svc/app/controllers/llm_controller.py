import logging
from datetime import date
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from svc.app.datatypes.week_activity import (BulkWeekActivityCreate,
                                             WeekActivityCreate,
                                             WeekActivityResponse)
from svc.app.dependencies import (CurrentUser, get_activity_service,
                                  get_current_user, get_week_activity_service)
from svc.app.llm.schemas.planner_schemas import (ActivityPlannerRequest,
                                                 PlannedActivity,
                                                 PlannedActivityLlmData)
from svc.app.llm.schemas.tagging_schemas import (ActivityTaggingRequest,
                                                 ActivityTaggingResponse,
                                                 TaggedActivity)
from svc.app.llm.services.planner_service import activity_planner_service
from svc.app.llm.services.tagging_service import activity_tagging_service
from svc.app.services.activity_service import ActivityService
from svc.app.services.week_activity_service import WeekActivityService
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/llm", tags=["LLM"])


@router.post("/tag-activities", response_model=ActivityTaggingResponse)
async def tag_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    request: ActivityTaggingRequest,
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
):
    """Tag activities using LLM"""
    try:
        # Get enum values from your existing models/services
        enums = activity_service.get_llm_enum_values()

        tagged_activities: List[TaggedActivity] = (
            await activity_tagging_service.tag_activities(request.activities, enums)
        )

        # Convert tag values from LLM to DB
        tagged_activities = [
            activity.convert_ai_to_db() for activity in tagged_activities
        ]

        # TODO: Can decide whether to auto save or require user to see it first then save
        #   for now we'll do auto save only
        # TODO: For now kids will be manual, llm auto tagging only works only on a family level
        # TODO: Check for duplicates, if activity already exists, don't create a new one
        # Save tagged activities to database
        saved_activities = activity_service.create_tagged_activities(
            tagged_activities, current_user.id
        )

        logger.info(
            f"Successfully saved {len(saved_activities)} tagged activities "
            f"for user {current_user.id}"
        )

        return ActivityTaggingResponse(
            tagged_activities=saved_activities, total_count=len(tagged_activities)
        )

    except LLMProcessingError as e:
        logger.error(f"LLM processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in tag_activities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/create-weekly-activities", response_model=List[WeekActivityResponse])
async def create_weekly_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    request: ActivityPlannerRequest,
    week_activity_service: WeekActivityService = Depends(get_week_activity_service),
):
    """Tag activities using LLM"""
    try:
        # TODO: Retrieve data from both backend and frontend that will be provided for llm
        llm_data: PlannedActivityLlmData = (
            activity_planner_service.retrieve_plan_weekly_activities_data()
        )
        planned_activities: List[PlannedActivity] = (
            await activity_planner_service.plan_weekly_activities(llm_data)
        )

        # TODO: Get date from frontend because of timezone differences
        current_date: date = (
            request.current_date if request.current_date else date.today()
        )
        bulk_data: BulkWeekActivityCreate = BulkWeekActivityCreate(
            assignments=[
                WeekActivityCreate(
                    activity_id=pa.activity_id, activity_date=current_date
                )
                for pa in planned_activities
            ]
        )
        return week_activity_service.bulk_create_week_activities(
            current_user.id, bulk_data
        )

    except LLMProcessingError as e:
        logger.error(f"LLM processing error: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in tag_activities: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
