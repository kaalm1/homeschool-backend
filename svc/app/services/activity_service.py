from typing import List, Optional

from svc.app.datatypes.enums import (
    AgeGroup,
    Cost,
    Duration,
    Location,
    Participants,
    Season,
)

from ..dal.activity_repository import ActivityRepository
from ..dal.kid_repository import KidRepository
from ..datatypes.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    RewardSummary,
)
from ..models.activity import Activity
from ..utils.exceptions import NotFoundError, ValidationError


class ActivityService:
    """Activity service for handling activity operations."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        kid_repository: KidRepository = None,
    ):
        self.activity_repo = activity_repository
        self.kid_repo = kid_repository

    def get_activities_by_parent(self, parent_id: int) -> List[ActivityResponse]:
        """Get all activities for a parent's kids."""
        activities = self.activity_repo.get_by_parent_id(parent_id)
        return [ActivityResponse.model_validate(activity) for activity in activities]

    def get_activities_by_kid(
        self, kid_id: int, parent_id: int
    ) -> List[ActivityResponse]:
        """Get all activities for a specific kid."""
        # Verify kid belongs to parent if kid_repo is available
        if self.kid_repo:
            kid = self.kid_repo.get_kid_by_parent(kid_id, parent_id)
            if not kid:
                raise NotFoundError("Kid not found")

        activities = self.activity_repo.get_by_kid_id(kid_id)
        return [ActivityResponse.model_validate(activity) for activity in activities]

    def create_activity(
        self, activity_data: ActivityCreate, parent_id: int
    ) -> ActivityResponse:
        """Create a new activity."""
        # Verify kid belongs to parent if kid_repo is available
        if self.kid_repo:
            kid = self.kid_repo.get_kid_by_parent(activity_data.kid_id, parent_id)
            if not kid:
                raise NotFoundError("Kid not found")

        activity = self.activity_repo.create_activity(
            title=activity_data.title,
            kid_id=activity_data.kid_id,
        )
        return ActivityResponse.model_validate(activity)

    def update_activity(
        self, activity_id: int, activity_data: ActivityUpdate, parent_id: int
    ) -> ActivityResponse:
        """Update an activity."""
        # Ensure activity belongs to parent
        existing_activity = self.activity_repo.get_activity_by_parent(
            activity_id, parent_id
        )
        if not existing_activity:
            raise NotFoundError("Activity not found")

        update_dict = activity_data.model_dump(exclude_unset=True)
        updated_activity = self.activity_repo.update(activity_id, update_dict)

        return ActivityResponse.model_validate(updated_activity)

    def toggle_activity(self, activity_id: int, parent_id: int) -> ActivityResponse:
        """Toggle activity completion status."""
        # Ensure activity belongs to parent
        existing_activity = self.activity_repo.get_activity_by_parent(
            activity_id, parent_id
        )
        if not existing_activity:
            raise NotFoundError("Activity not found")

        updated_activity = self.activity_repo.toggle_done_status(activity_id)
        return ActivityResponse.model_validate(updated_activity)

    def delete_activity(self, activity_id: int, parent_id: int) -> bool:
        """Delete an activity."""
        # Ensure activity belongs to parent
        existing_activity = self.activity_repo.get_activity_by_parent(
            activity_id, parent_id
        )
        if not existing_activity:
            raise NotFoundError("Activity not found")

        return self.activity_repo.delete(activity_id)

    def get_reward_summary(self, parent_id: int) -> List[RewardSummary]:
        """Get reward summary for all kids."""
        if not self.kid_repo:
            raise ValidationError("Kid repository not available")

        kids = self.kid_repo.get_by_parent_id(parent_id)
        summary = []

        for kid in kids:
            completed_count = self.activity_repo.get_completed_count_by_kid(kid.id)
            summary.append(
                RewardSummary(kid_id=kid.id, kid_name=kid.name, stars=completed_count)
            )

        return summary

    def search_activities(
        self,
        cost: Optional[List[Cost]] = None,
        duration: Optional[List[Duration]] = None,
        participants: Optional[List[Participants]] = None,
        locations: Optional[List[Location]] = None,
        seasons: Optional[List[Season]] = None,
        age_groups: Optional[List[AgeGroup]] = None,
        themes: Optional[List[str]] = None,
        activity_types: Optional[List[str]] = None,
    ):
        return self.activity_repo.filter_activities(
            cost=cost,
            duration=duration,
            participants=participants,
            locations=locations,
            seasons=seasons,
            age_groups=age_groups,
            themes=themes,
            activity_types=activity_types,
        )
