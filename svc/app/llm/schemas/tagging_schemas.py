import json
from typing import List

from pydantic import BaseModel, Field

from svc.app.datatypes.enums import FilterEnum


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

    def convert_ai_to_db(self) -> dict:
        """Get a summary of how AI values were converted to DB values."""
        activity_data = self.model_dump()
        converted_data = FilterEnum.bulk_convert_from_ai(activity_data)

        self.themes = converted_data["themes"]
        self.activity_types = converted_data["activity_types"]
        self.costs = converted_data["costs"]
        self.durations = converted_data["durations"]
        self.participants = converted_data["participants"]
        self.locations = converted_data["locations"]
        self.seasons = converted_data["seasons"]
        self.age_groups = converted_data["age_groups"]
        self.frequency = converted_data["frequency"]

        return converted_data


class ActivityTaggingResponse(BaseModel):
    tagged_activities: List[TaggedActivity]
    total_count: int
