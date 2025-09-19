import json
import logging
from typing import Any, Dict, List, Optional

from svc.app.config import settings
from svc.app.datatypes.enums import DEFAULT_ENUMS_LLM
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.activity_tagging import (
    ACTIVITY_TAGGING_SYSTEM_PROMPT,
    build_activity_tagging_prompt,
)
from svc.app.llm.schemas.tagging_schemas import TaggedActivity
from svc.app.llm.utils.parsers import parse_response_to_json

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
        schema = self.build_activity_tagging_schema(enums)
        logger.info(prompt)

        try:
            response = llm_client.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": ACTIVITY_TAGGING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=self.temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "activity_array",
                        "schema": schema,
                    },
                },
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from LLM")
                return []

            content_parsed: list = parse_response_to_json(content)
            # Validate structure
            self._validate_tagged_activities(content_parsed, enums)
            # Parse and validate JSON
            tagged_activities: List[TaggedActivity] = TaggedActivity.from_json(
                content_parsed
            )
            if not isinstance(tagged_activities, list):
                logger.error("LLM response is not a JSON array")
                return []

            logger.info(f"Successfully tagged {len(tagged_activities)} activities")
            return tagged_activities

        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"LLM tagging error: {e}")

    def build_activity_tagging_schema(
        self, enums: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build a JSON schema for activity tagging with enum restrictions
        derived from DEFAULT_ENUMS_LLM.
        """
        if enums is None:
            enums = DEFAULT_ENUMS_LLM

        # base object schema
        properties: Dict[str, Any] = {
            "title": {"type": "string", "maxLength": 50},  # enforce 8 words-ish
            "description": {"type": "string", "maxLength": 300},
            "price": {"type": "number"},
            "price_verified": {"type": "boolean"},
            "website": {"type": "string"},
        }
        required = ["title", "description"]

        # add enums dynamically
        for key, (values, value_type) in enums.items():
            if value_type == "list":
                properties[key] = {
                    "type": "array",
                    "items": {"type": "string", "enum": values},
                    "uniqueItems": True,
                }
            elif value_type == "string":
                properties[key] = {"type": "string", "enum": values}

        # add convenience single-value enums for primary type/theme if present
        if "activity_types" in enums:
            properties["primary_type"] = {
                "type": "string",
                "enum": enums["activity_types"][0],
            }
        if "themes" in enums:
            properties["primary_theme"] = {"type": "string", "enum": enums["themes"][0]}

        return {
            "type": "array",
            "items": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
            "minItems": 1,
            # "maxItems": 20,  # you can cap this
        }

    def _validate_tagged_activities(
        self, activities: List[Dict], enums: Dict[str, Any]
    ) -> None:
        """Validate and clean the structure of tagged activities against enum definitions"""
        valid_keys = set(enums.keys())

        for activity in activities:
            # --- Clean values for each enum key ---
            for enum_field, (allowed_values, value_type) in enums.items():
                if enum_field in activity:
                    current_values = activity[enum_field]

                    if isinstance(current_values, list):
                        valid_values = [
                            v for v in current_values if v in allowed_values
                        ]
                        invalid_values = set(current_values) - set(valid_values)

                        if invalid_values:
                            logger.error(
                                f"Removed invalid {enum_field} values: {invalid_values}"
                            )

                        activity[enum_field] = valid_values
                    elif isinstance(current_values, str):
                        activity[enum_field] = (
                            current_values
                            if current_values in allowed_values
                            else None
                        )


# Singleton instance
activity_tagging_service = ActivityTaggingService()
