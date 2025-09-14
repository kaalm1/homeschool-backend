from svc.app.config import settings
from svc.app.datatypes.family_preference import FamilyProfile
from svc.app.llm.client import llm_client
from svc.app.services.family_profile_service import FamilyProfileService


class ActivityChecklistService:
    def __init__(self, family_profile_service: FamilyProfileService):
        self.family_profile_service = family_profile_service
        self.llm_client = llm_client
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries
        self.system_prompt = """
        You are a helpful assistant that turns family activities into ADHD-friendly checklists.

        Your job:
        - Take an activity and optional family context.
        - Return a structured JSON object only.
        - Do not include explanations, markdown, or extra text.

        The JSON object must have exactly these keys:
        {
          "equipment": [list of strings],
          "instructions": [list of strings],
          "adhd_tips": [list of strings]
        }

        Guidelines:
        - Be concrete and practical.
        - Adjust details based on context (ages of kids, family size, location, season).
        - Keep lists short, simple, and actionable.
        - Always return valid JSON.
        """

    def generate_checklist(
        self,
        user_id: int,
        activity: str,
    ) -> dict:
        profile: FamilyProfile = self.family_profile_service.get_family_profile(user_id)
        family_context = self._format_family_context(profile)

        response = self.llm_client.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": f"Activity: {activity}\nFamily context (JSON): {family_context}",
                },
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"},  # ensure valid JSON
        )

        return response.choices[0].message.parsed

    def _format_family_context(self, profile: FamilyProfile) -> dict:
        """Convert FamilyProfile into a structured JSON context with only relevant fields."""
        context = {
            "family_size": profile.family_size,
            "adults_count": profile.adults_count,
            "kids": [k.get("age", None) for k in profile.kids],  # just ages
            "location": profile.home_location,
            "has_car": profile.has_car,
            "max_travel_distance_km": profile.max_travel_distance,
        }

        if profile.weekly_activity_budget:
            context["weekly_activity_budget"] = profile.weekly_activity_budget
        if profile.preferred_cost_ranges:
            context["preferred_cost_ranges"] = profile.preferred_cost_ranges

        return context
