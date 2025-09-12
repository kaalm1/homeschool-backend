import json
import logging
from typing import Any, Dict, List

from svc.app.config import settings
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.activity_planner import (
    ACTIVITY_PLANNER_SYSTEM_PROMPT,
    build_activity_planner_prompt,
)
from svc.app.llm.schemas.planner_schemas import PlannedActivity, PlannedActivityLlmData
from svc.app.llm.utils.parsers import parse_response_to_json
from svc.app.services.activity_service import ActivityService
from svc.app.services.kid_service import KidService
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)


class ActivityPlannerService:
    def __init__(self, activity_service: ActivityService, kid_service: KidService):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries
        self.activity_service = activity_service
        self.kid_service = kid_service

    def retrieve_plan_weekly_activities_data(self) -> PlannedActivityLlmData:
        return PlannedActivityLlmData(family={}, context={}, activities=[])

    async def plan_weekly_activities(
        self, llm_data: PlannedActivityLlmData
    ) -> List[PlannedActivity]:
        """Tag activities using LLM"""
        prompt = build_activity_planner_prompt(
            llm_data.family, llm_data.context, llm_data.activities
        )
        logger.info(prompt)

        for attempt in range(self.max_retries + 1):
            try:
                response = llm_client.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": ACTIVITY_PLANNER_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                )

                content = response.choices[0].message.content
                if not content:
                    raise LLMProcessingError("Empty response from LLM")

                content_parsed: list = parse_response_to_json(content)
                # Validate structure
                self._validate_planned_activities(content_parsed)
                # Parse and validate JSON
                planned_activities: List[PlannedActivity] = PlannedActivity.from_json(
                    content_parsed
                )
                if not isinstance(planned_activities, list):
                    raise LLMProcessingError("LLM response is not a JSON array")

                logger.info(
                    f"Successfully planned {len(planned_activities)} activities"
                )
                return planned_activities

            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    raise LLMProcessingError(
                        f"Failed to parse JSON after {self.max_retries + 1} attempts"
                    )

            except Exception as e:
                logger.error(f"LLM tagging error on attempt {attempt + 1}: {e}")
                if attempt == self.max_retries:
                    raise LLMProcessingError(f"LLM tagging failed: {str(e)}")

    def _validate_planned_activities(self, activities: List[Dict]):
        """Validate and clean the structure of tagged activities against enum definitions"""
        validated = []

        for i, item in enumerate(activities):
            if isinstance(item, dict):
                activity_id = item.get("id")
                if not isinstance(activity_id, int):
                    logger.warning(
                        f"Removed non-integer value '{activity_id}' (type: {type(activity_id).__name__}) at index {i}"
                    )

        return validated
