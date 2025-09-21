import json
import logging

from svc.app.config import settings
from svc.app.datatypes.activity import ActivityResponse, ActivityUpdate
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.llm.client import llm_client
from svc.app.llm.prompts.checklist_creation import ActivityChecklistPrompts
from svc.app.llm.utils.parsers import parse_response_to_json
from svc.app.models.activity import Activity
from svc.app.services.activity_service import ActivityService
from svc.app.services.family_profile_service import FamilyProfileService

logger = logging.getLogger(__name__)


class ChecklistCreationService:
    def __init__(
        self,
        activity_service: ActivityService,
        family_profile_service: FamilyProfileService,
    ):
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries
        self.prompts = ActivityChecklistPrompts()
        self.activity_service = activity_service
        self.family_profile_service = family_profile_service

    async def create_checklist(
        self, activity_id: int, user_id: int
    ) -> ActivityResponse:
        """Tag activities using LLM"""
        activity: ActivityResponse = self.activity_service.get_activity(
            activity_id, user_id
        )
        family_profile: FamilyProfile = self.family_profile_service.get_family_profile(
            user_id
        )
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
                        "schema": self.prompts.schema,
                    },
                },
            )
            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response from LLM")
                return ActivityResponse.model_validate(activity)

            content_parsed: dict = parse_response_to_json(content)[0]

            activity_update = ActivityUpdate(**content_parsed)
            activity = self.activity_service.update_activity(
                activity.id, activity_update, user_id
            )

            return activity

        except json.JSONDecodeError as e:
            logger.exception(f"JSON decode error: {e}")
        except Exception as e:
            logger.exception(f"LLM tagging error: {e}")
