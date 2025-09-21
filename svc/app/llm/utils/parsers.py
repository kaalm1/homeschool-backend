import json
import re
from typing import Dict, List, Union


def parse_response_to_json(content: str) -> List[Dict[str, List[str]]]:
    """
    Parse LLM response content into JSON.
    Handles cases where the JSON is wrapped in ```json ... ``` blocks.
    Can return either a list or dict at the root, but always normalizes to a list.
    """
    if not content:
        return []

    # Remove ```json ... ``` or ``` wrappers if present
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.DOTALL)

    try:
        parsed: Union[List[Dict[str, List[str]]], Dict[str, List[str]]] = json.loads(
            cleaned
        )

        if isinstance(parsed, dict):
            # Wrap single dict into a list
            return [parsed]
        elif isinstance(parsed, list):
            return parsed
        else:
            raise ValueError(f"Unexpected JSON structure: {type(parsed)}")

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse response as JSON: {e}\nContent was:\n{content}"
        )
