import json
import logging
from typing import Any, Dict, List

from svc.app.llm.client import llm_client
from svc.app.llm.prompts.activity_tagging import (
    ACTIVITY_TAGGING_SYSTEM_PROMPT, build_activity_tagging_prompt)
from svc.app.llm.schemas.tagging_schemas import TaggedActivity
from svc.app.utils.exceptions import LLMProcessingError

logger = logging.getLogger(__name__)


class ActivityTaggingService:
    def __init__(self):
        self.model = "gpt-4o-mini"  # or gpt-4 for better quality
        self.temperature = 0
        self.max_retries = 2

    async def tag_activities(
        self, activities: str, enums: Dict[str, Any]
    ) -> List[Dict[str, List[str]]]:
        """Tag activities using LLM"""
        prompt = build_activity_tagging_prompt(activities, enums)

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

                # Parse and validate JSON
                tagged_activities: List[TaggedActivity] = TaggedActivity.parse_response(
                    content
                )
                if not isinstance(tagged_activities, list):
                    raise LLMProcessingError("LLM response is not a JSON array")

                # Validate structure
                self._validate_tagged_activities(tagged_activities, enums)

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
        """Validate the structure and enum values of tagged activities"""
        required_fields = [
            "activity",
            "themes",
            "activity_types",
            "costs",
            "durations",
            "participants",
            "locations",
            "seasons",
            "age_groups",
        ]

        for activity in activities:
            # Check required fields
            for field in required_fields:
                if field not in activity:
                    raise LLMProcessingError(f"Missing required field: {field}")

            # Validate enum constraints
            for enum_field in [
                "costs",
                "durations",
                "participants",
                "locations",
                "seasons",
                "age_groups",
                "themes",
                "activity_types",
            ]:
                if enum_field in enums:
                    invalid_values = set(activity[enum_field]) - set(enums[enum_field])
                    if invalid_values:
                        raise LLMProcessingError(
                            f"Invalid {enum_field} values: {invalid_values}"
                        )


# Singleton instance
activity_tagging_service = ActivityTaggingService()
