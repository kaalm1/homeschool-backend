import json
from typing import List

from pydantic import BaseModel, Field


class ActivityTaggingRequest(BaseModel):
    activities: str = Field(..., description="Raw activities text to be tagged")


class TaggedActivity(BaseModel):
    title: str
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

    def to_db_dict(self) -> dict:
        """Convert TaggedActivity to a dictionary suitable for database insertion."""
        return {
            "title": self.title,
            "themes": self.themes,
            "activity_types": self.activity_types,
            "costs": self.costs,
            "durations": self.durations,
            "participants": self.participants,
            "locations": self.locations,
            "seasons": self.seasons,
            "age_groups": self.age_groups,
            "frequency": self.frequency,
        }

    @classmethod
    def to_db_dict_list(cls, tagged_activities: List["TaggedActivity"]) -> List[dict]:
        """Convert a list of TaggedActivity objects to database-ready dictionaries."""
        return [activity.to_db_dict() for activity in tagged_activities]


class ActivityTaggingResponse(BaseModel):
    tagged_activities: List[TaggedActivity]
    total_count: int
