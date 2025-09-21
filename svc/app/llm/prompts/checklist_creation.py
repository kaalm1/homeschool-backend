from svc.app.models.activity import Activity
from svc.app.datatypes.family_preference import FamilyProfile


class ActivityChecklistPrompts:
    def __init__(self):
        self.system_prompt = """
            You are a helpful assistant that turns family activities into ADHD-friendly checklists.
    
            Your job:
            - Take an activity and structured family context.
            - Return a structured JSON object only.
            - Do not include explanations, markdown, or extra text.
    
            The JSON object must have exactly these keys:
            {
              "equipment": [list of strings],
              "steps": [list of strings],
              "adhd_tips": [list of strings]
            }
    
            Guidelines:
            - Be concrete and practical.
            - Adjust details based on family profile (demographics, location, budget, time, preferences).
            - Keep lists short, simple, and actionable.
            - Always return valid JSON.
            """

    def build_user_prompt(
        self, activity: Activity, family_profile: FamilyProfile
    ) -> str:
        return f"Activity: {activity}\nFamily context:\n{self._format_family_context(family_profile)}"

    def _format_activity_context(self, activity: Activity) -> str:
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
            f"Location: {profile.home_location}, max travel distance: {profile.max_travel_distance} km",
            f"Transportation: {'car available' if profile.has_car else 'no car'}",
        ]

        if profile.weekly_activity_budget:
            context_parts.append(
                f"Weekly activity budget: ${profile.weekly_activity_budget}"
            )
        if profile.preferred_cost_ranges:
            context_parts.append(
                f"Preferred cost ranges: {', '.join(profile.preferred_cost_ranges)}"
            )
        if profile.available_days:
            context_parts.append(
                f"Available days: {', '.join([d.name for d in profile.available_days])}"
            )
        if profile.preferred_time_slots:
            context_parts.append(
                f"Preferred time slots: {', '.join([t.name for t in profile.preferred_time_slots])}"
            )
        if profile.preferred_themes:
            context_parts.append(
                f"Preferred themes: {', '.join([t.name for t in profile.preferred_themes])}"
            )
        if profile.preferred_activity_types:
            context_parts.append(
                f"Preferred activity types: {', '.join([a.name for a in profile.preferred_activity_types])}"
            )
        if profile.group_activity_comfort:
            context_parts.append(
                f"Group comfort level: {profile.group_activity_comfort.name}"
            )
        if profile.new_experience_openness:
            context_parts.append(
                f"New experience openness: {profile.new_experience_openness.name}"
            )

        return "\n".join(context_parts)
