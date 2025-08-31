from typing import Any, Dict, Optional

from svc.app.datatypes.enums import DEFAULT_ENUMS_AI

ACTIVITY_TAGGING_SYSTEM_PROMPT = "You are a JSON tagging engine for a family activity planner. Return only valid JSON."


def build_activity_tagging_prompt(
    activities: str, enums: Optional[Dict[str, Any]] = None
) -> str:
    if enums is None:
        enums = DEFAULT_ENUMS_AI

    # dynamically build the lines for each enum key
    enum_lines = []
    for key, values in enums.items():
        enum_lines.append(f"- {key} (list): Must be subset of {values}")

    enum_text = "\n".join(enum_lines)

    return f"""
Split the following into individual activities and tag them.
Return JSON list where each object has:
- activity (string): The activity name
{enum_text}

Activities:
{activities}

Return only the JSON array, no other text.
"""
