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
    for key, (values, value_type) in enums.items():
        if value_type == "list":
            enum_lines.append(f"- {key} (list): Must be subset of {values}")
        elif value_type == "string":
            enum_lines.append(f"- {key} (string): Must be a single value from {values}")

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

You must carefully parse free-form, messy text into **distinct activities**. 
Writers may have ADHD and use inconsistent formatting: missing commas, missing 'and', 
line breaks, or streams of thought.

Rules:
- Each activity should represent something a family could realistically do as a 
  separate outing or task. 
- Treat line breaks, commas, 'and', or sudden topic changes as potential boundaries. 
- If two concepts are different activities (e.g., 'splashpad apple picking'), 
  split them into two. 
- If words clearly belong together as one activity (e.g., 'arts and crafts', 
  'playdate with Barbara and Tina', 'making pizza with cheese and sauce'), 
  keep them together. 
- When in doubt, err on the side of **separating into multiple activities** 
  instead of merging too much.

After splitting, tag each activity according to the allowed filters below.


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
