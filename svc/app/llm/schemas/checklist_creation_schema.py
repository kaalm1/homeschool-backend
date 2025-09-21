from typing import List

from pydantic import BaseModel, Field

from svc.app.models.activity import Activity


class ChecklistCreation(BaseModel):
    activity: Activity = Field(..., description="Raw activities text to be tagged")
    equipment: List[str] = Field()
    steps: List[str] = Field()
    adhd_tips: List[str] = Field()

    @classmethod
    def from_json(cls, content: dict) -> "ChecklistCreation":
        """Parse a JSON string into a ChecklistCreation object."""
        return cls(**content)