from typing import Any, Dict, Optional

from svc.app.datatypes.enums import DEFAULT_ENUMS_LLM

ACTIVITY_TAGGING_SYSTEM_PROMPT = "You are a JSON tagging engine for a family activity planner. Return only valid JSON."


def build_activity_tagging_prompt(
    activities: str, enums: Optional[Dict[str, Any]] = None
) -> str:
    if enums is None:
        enums = DEFAULT_ENUMS_LLM

    # dynamically build the lines for each enum key
    enum_lines = []
    for key, values in enums.items():
        enum_lines.append(f"- {key} (list): Must be subset of {values}")

    enum_text = "\n".join(enum_lines)

    return f"""
You are a JSON tagging engine for a family activity planner. Your tasks:
1. Split the following free-form text into individual activities. Activities may be completely free form, sentences, phrases, or comma-separated.
2. Tag each activity according to the allowed filters below.

Return JSON list where each object has:
- activity (string): The activity (as concise and clear as possible, preferably no longer than a sentence)
{enum_text}

Activities:
{activities}

Return only the JSON array. Each activity must be split and tagged appropriately.
Do not include any other text or explanation.
"""
