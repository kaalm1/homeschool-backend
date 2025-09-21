import json
import logging
from typing import Any, Dict, List, Optional

from svc.app.config import settings
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.checklist_creation import ActivityChecklistPrompts
from svc.app.llm.utils.parsers import parse_response_to_json
from svc.app.models.activity import Activity
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.llm.schemas.checklist_creation_schema import ChecklistCreation

logger = logging.getLogger(__name__)

class ChecklistCreationService:
    def __init__(self):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries
        self.prompts = ActivityChecklistPrompts()

    async def checklist_creation(
        self, activity: Activity, family_profile: FamilyProfile
    ) -> Optional[ChecklistCreation]:
        """Tag activities using LLM"""
        user_prompt = self.prompts.build_user_prompt(activity, family_profile)

        try:
            response = llm_client.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.prompts.system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "checklist_array",
                        "schema": schema,
                    },
                },
            )

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from LLM")
                return None

            content_parsed: list = parse_response_to_json(content)

            # Parse and validate JSON
            activity_with_checklist: ChecklistCreation = ChecklistCreation.from_json(
                content_parsed
            )

            return activity_with_checklist

        except json.JSONDecodeError as e:
            logger.exception(f"JSON decode error: {e}")
        except Exception as e:
            logger.exception(f"LLM tagging error: {e}")