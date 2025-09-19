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
        if values[1] == 'list':
            enum_lines.append(f"- {key} (list): Must be subset of {values[0]}")
        elif values[1] == 'string':
            enum_lines.append(
                f"- {key} (string): Must be a single value from {values[0]}"
            )

    # add primary_type rule if activity_types exists
    if "activity_types" in enums:
        enum_lines.append(
            f"- primary_type (string): Must be a single value from {enums['activity_types']}"
        )

    if "themes" in enums:
        enum_lines.append(
            f"- primary_theme (string): Must be a single value from {enums['themes']}"
        )

    enum_text = "\n".join(enum_lines)

    return f"""
You are a JSON tagging engine for a family activity planner. Your tasks:
1. Split the following free-form text into individual activities. Activities may be completely free form, sentences, phrases, or comma-separated.
2. Tag each activity according to the allowed filters below.

Return JSON list where each object has:
- title (string): Clear activity name, **must be 8 words or less**
- description (string): Up to two sentences, clear but concise
- price (float, optional): Estimated or verified price in numeric format. Only include if a reasonable estimate or verified value is available. If the activity is free, use 0.0.
- price_verified (boolean, optional): true if the price is verified, false if it is a guesstimate. Only include if price is provided.
- website (string, optional): Include if a known or plausible website exists
{enum_text}

Activities:
{activities}

Return only the JSON array. Each activity must be split and tagged appropriately.
Do not include any other text or explanation.
"""
