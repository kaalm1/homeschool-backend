from svc.app.datatypes.activity import ActivityResponse
from svc.app.datatypes.family_preference import FamilyProfile


class ActivityChecklistPrompts:
    def __init__(self):
        self.schema = schema = {
            "type": "object",
            "properties": {
                "equipment": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of equipment or materials needed for the activity.",
                },
                "instructions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Step-by-step instructions for completing the activity.",
                },
                "adhd_tips": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Simple, ADHD-friendly tips to make the activity easier to follow.",
                },
            },
            "required": ["equipment", "instructions", "adhd_tips"],
            "additionalProperties": False,
        }

        self.system_prompt = """
            You are a helpful assistant that turns family activities into ADHD-friendly checklists.
    
            Your job:
            - Take an activity and structured family context.
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
            - Adjust details based on family profile (demographics, location, budget, time, preferences).
            - Keep lists short, simple, and actionable.
            - Always return valid JSON.
            """

    def build_user_prompt(
        self, activity: ActivityResponse, family_profile: FamilyProfile
    ) -> str:
        return f"Activity: {activity}\nFamily context:\n{self._format_family_context(family_profile)}"

    def _format_activity_context(self, activity: ActivityResponse) -> str:
        return f"{activity.title} {activity.description}"

    def _format_family_context(self, profile: FamilyProfile) -> str:
        """Convert FamilyProfile into concise plain-text context for the prompt."""
        kids_desc = (
            ", ".join(
                f"{k.get('age', '?')}yo"
                + (f" ({k.get('notes')})" if k.get("notes") else "")
                for k in profile.kids
            )
            if profile.kids
            else "no kids"
        )

        context_parts = [
            f"Family size: {profile.family_size} (adults: {profile.adults_count}, kids: {kids_desc})",
            f"Location: {profile.zipcode}, max travel distance: {profile.max_travel_distance} km",
            f"Transportation: {'car available' if profile.has_car else 'no car'}",
        ]

        return "\n".join(context_parts)
