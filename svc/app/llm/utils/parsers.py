import json
import re
from typing import Dict, List


def parse_response_to_json(content: str) -> List[Dict[str, List[str]]]:
    """
    Parse LLM response content into JSON.
    Handles cases where the JSON is wrapped in ```json ... ``` blocks.
    """
    if not content:
        return []

    # Remove ```json ... ``` or ``` wrappers if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.DOTALL)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse response as JSON: {e}\nContent was:\n{content}"
        )
