from typing import Any, Dict

ACTIVITY_TAGGING_SYSTEM_PROMPT = "You are a JSON tagging engine for a family activity planner. Return only valid JSON."


def build_activity_tagging_prompt(activities: str, enums: Dict[str, Any]) -> str:
    return f"""
Split the following into individual activities and tag them.
Return JSON list where each object has:
- activity (string): The activity name
- themes (list): Must be subset of {enums.get('themes', [])}
- activity_types (list): Must be subset of {enums.get('activity_types', [])}
- costs (list): Must be subset of {enums.get('cost', [])}
- durations (list): Must be subset of {enums.get('duration', [])}
- participants (list): Must be subset of {enums.get('participant', [])}
- locations (list): Must be subset of {enums.get('location', [])}
- seasons (list): Must be subset of {enums.get('season', [])}
- age_groups (list): Must be subset of {enums.get('age_group', [])}
- themes (list): Must be subset of {enums.get('themes', [])}
- activity_types (list): Must be subset of {enums.get('activity_types', [])}

Activities:
{activities}

Return only the JSON array, no other text.
"""
