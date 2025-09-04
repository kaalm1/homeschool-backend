import json
from typing import List, Optional

from pydantic import BaseModel, Field

class PlannedActivity(BaseModel):
    activity_id: int

    @classmethod
    def from_llm(cls, content: str) -> List["PlannedActivity"]:
        """Parse a JSON string into a list of PlannedActivity objects."""
        raw_data = json.loads(content)  # list of dicts
        return [cls(**item) for item in raw_data]

    @classmethod
    def from_json(cls, content: list) -> List["TaggedActivity"]:
        """Parse a JSON string into a list of TaggedActivity objects."""
        return [cls(**item) for item in content]

