from typing import List, Optional

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


class ActivityTaggingResponse(BaseModel):
    tagged_activities: List[TaggedActivity]
    total_count: int
