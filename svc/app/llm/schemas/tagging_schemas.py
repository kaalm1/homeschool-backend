import json
from typing import List, Optional

from pydantic import BaseModel, Field

from svc.app.datatypes.activity import ActivityResponse
from svc.app.datatypes.enums import FilterEnum


class ActivityTaggingRequest(BaseModel):
    activities: str = Field(..., description="Raw activities text to be tagged")


class TaggedActivity(BaseModel):
    title: str
    description: Optional[str] = None
    price: Optional[float] = None
    price_verified: Optional[bool] = None
    primary_type: Optional[str] = None
    primary_theme: Optional[str] = None
    website: Optional[str] = None
    themes: List[str] = []
    activity_types: List[str] = []
    costs: List[str] = []
    durations: List[str] = []
    participants: List[str] = []
    locations: List[str] = []
    seasons: List[str] = []
    age_groups: List[str] = []
    frequency: List[str] = []
    activity_scale: Optional[str] = None

    @classmethod
    def from_llm(cls, content: str) -> List["TaggedActivity"]:
        """Parse a JSON string into a list of TaggedActivity objects."""
        raw_data = json.loads(content)  # list of dicts
        return [cls(**item) for item in raw_data]

    @classmethod
    def from_json(cls, content: list) -> List["TaggedActivity"]:
        """Parse a JSON string into a list of TaggedActivity objects."""
        return [cls(**item) for item in content]

    def to_db_dict(self) -> dict:
        """Convert TaggedActivity to a dictionary suitable for database insertion."""
        return {
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "price_verified": self.price_verified,
            "primary_type": self.primary_type,
            "primary_theme": self.primary_theme,
            "themes": self.themes,
            "activity_types": self.activity_types,
            "costs": self.costs,
            "durations": self.durations,
            "participants": self.participants,
            "locations": self.locations,
            "seasons": self.seasons,
            "age_groups": self.age_groups,
            "frequency": self.frequency,
            "activity_scale": self.activity_scale,
        }

    @classmethod
    def to_db_dict_list(cls, tagged_activities: List["TaggedActivity"]) -> List[dict]:
        """Convert a list of TaggedActivity objects to database-ready dictionaries."""
        return [activity.to_db_dict() for activity in tagged_activities]

    def convert_ai_to_db(self) -> "TaggedActivity":
        """Convert AI values to DB values."""
        activity_data = self.model_dump()
        converted_data = FilterEnum.bulk_convert_from_ai(activity_data)

        for key in [
            "themes",
            "activity_types",
            "costs",
            "durations",
            "participants",
            "locations",
            "seasons",
            "age_groups",
            "frequency",
            "primary_type",
            "primary_theme",
            "activity_scale",
        ]:
            if key in converted_data:
                setattr(self, key, converted_data[key])

        return self


class ActivityTaggingResponse(BaseModel):
    tagged_activities: List[ActivityResponse]
    total_count: int
