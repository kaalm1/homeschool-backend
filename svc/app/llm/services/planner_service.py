import json
import logging
from typing import Any, Dict, List

from svc.app.config import settings
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.activity_planner import build_activity_planner_prompt, ACTIVITY_PLANNER_SYSTEM_PROMPT
from svc.app.llm.utils.parsers import parse_response_to_json
from svc.app.utils.exceptions import LLMProcessingError
from svc.app.llm.schemas.planner_schemas import PlannedActivity

logger = logging.getLogger(__name__)


class ActivityPlannerService:
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries

    async def plan_weekly_activities(
        self, family: dict, context: dict, activities: List[dict]
    ) -> List[PlannedActivity]:
        """Tag activities using LLM"""
        prompt = build_activity_planner_prompt(family, context, activities)
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

                logger.info(f"Successfully planned {len(planned_activities)} activities")
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

    def _validate_planned_activities(
            self, activities: List[Dict]
    ):
        """Validate and clean the structure of tagged activities against enum definitions"""
        validated = []

        for i, item in enumerate(activities):
            if isinstance(item, int):
                validated.append(item)
            else:
                logger.warning(f"Removed non-integer value '{item}' (type: {type(item).__name__}) at index {i}")

        return validated



activity_planner_service = ActivityPlannerService()