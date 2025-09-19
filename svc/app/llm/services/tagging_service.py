import json
import logging
from typing import Any, Dict, List

from svc.app.config import settings
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.activity_tagging import (
    ACTIVITY_TAGGING_SYSTEM_PROMPT,
    build_activity_tagging_prompt,
)
from svc.app.llm.schemas.tagging_schemas import TaggedActivity
from svc.app.llm.utils.parsers import parse_response_to_json
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)


class ActivityTaggingService:
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries

    async def tag_activities(
        self, activities: str, enums: Dict[str, Any]
    ) -> List[TaggedActivity]:
        """Tag activities using LLM"""
        prompt = build_activity_tagging_prompt(activities, enums)
        logger.info(prompt)

        for attempt in range(self.max_retries + 1):
            try:
                response = llm_client.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": ACTIVITY_TAGGING_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                )

                content = response.choices[0].message.content
                if not content:
                    raise LLMProcessingError("Empty response from LLM")

                content_parsed: list = parse_response_to_json(content)
                # Validate structure
                self._validate_tagged_activities(content_parsed, enums)
                # Parse and validate JSON
                tagged_activities: List[TaggedActivity] = TaggedActivity.from_json(content_parsed)
                if not isinstance(tagged_activities, list):
                    raise LLMProcessingError("LLM response is not a JSON array")

                logger.info(f"Successfully tagged {len(tagged_activities)} activities")
                return tagged_activities

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

    def _validate_tagged_activities(
        self, activities: List[Dict], enums: Dict[str, Any]
    ):
        """Validate and clean the structure of tagged activities against enum definitions"""
        valid_keys = set(enums.keys())

        for activity in activities:
            # --- Clean values for each enum key ---
            for enum_field, allowed_values in enums.items():
                if enum_field in activity:
                    current_values = activity[enum_field]

                    if isinstance(current_values, list):
                        valid_values = [v for v in current_values if v in allowed_values[0]]
                        invalid_values = set(current_values) - set(valid_values)

                        if invalid_values:
                            logger.error(
                                f"Removed invalid {enum_field} values: {invalid_values}"
                            )

                        activity[enum_field] = valid_values


# Singleton instance
activity_tagging_service = ActivityTaggingService()
