import json
from typing import List

from pydantic import BaseModel, Field


class ActivityTaggingRequest(BaseModel):
    activities: str = Field(..., description="Raw activities text to be tagged")


class TaggedActivity(BaseModel):
    activity: str
    themes: List[str] = []
    activity_types: List[str] = []
    costs: List[str] = []
    durations: List[str] = []
    participants: List[str] = []
    locations: List[str] = []
    seasons: List[str] = []
    age_groups: List[str] = []
    frequency: List[str] = []

    @classmethod
    def from_json(cls, content: str) -> List["TaggedActivity"]:
        """Parse a JSON string into a list of TaggedActivity objects."""
        raw_data = json.loads(content)  # list of dicts
        return [cls(**item) for item in raw_data]


class ActivityTaggingResponse(BaseModel):
    tagged_activities: List[TaggedActivity]
    total_count: int
