import json
import re
from typing import Any


def parse_content(content: Any) -> list:
    try:
        if isinstance(content, list):
            activities = content
        else:
            start = content.find("[")
            if start != -1:
                content = content[start:]
            activities = json.loads(content.strip())
    except json.JSONDecodeError:
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", content, re.DOTALL)
        if json_match:
            activities = json.loads(json_match.group(1))
        else:
            return []

    return activities
