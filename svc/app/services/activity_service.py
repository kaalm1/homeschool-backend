import logging
from typing import List, Optional

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.dal.kid_repository import KidRepository
from svc.app.datatypes.activity import (
    ActivityCreate,
    ActivityResponse,
    ActivityUpdate,
    RewardSummary,
)
from svc.app.datatypes.enums import (
    DEFAULT_ENUMS_LLM,
    AgeGroup,
    Cost,
    Duration,
    Location,
    Participants,
    Season,
)
from svc.app.llm.schemas.tagging_schemas import TaggedActivity
from svc.app.models.activity import Activity
from svc.app.utils.exceptions import NotFoundError, ValidationError

logger = logging.getLogger(__name__)


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

    def create_tagged_activities(
        self, activities_data: List[TaggedActivity], user_id: int
    ) -> List[ActivityResponse]:
        """Create multiple tagged activities from LLM response."""
        try:
            # Use the repository method to create activities
            activities_data = self.filter_missing_titles(activities_data)
            activities_created: List[Activity] = (
                self.activity_repo.create_tagged_activities(
                    TaggedActivity.to_db_dict_list(activities_data), user_id
                )
            )
            return [
                ActivityResponse.model_validate(activity)
                for activity in activities_created
            ]
        except Exception as e:
            logger.error(f"Error creating tagged activities for user {user_id}: {e}")
            raise

    def bulk_create_activities(self, activities_data: List[dict]) -> List[Activity]:
        """Bulk create activities for better performance with large datasets."""
        try:
            return self.activity_repo.bulk_create_activities(activities_data)
        except Exception as e:
            logger.error(f"Error bulk creating activities: {e}")
            raise

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

    def get_llm_enum_values(self):
        return DEFAULT_ENUMS_LLM

    def filter_missing_titles(
        self, tagged_activities: List[TaggedActivity]
    ) -> List[TaggedActivity]:
        return [activity for activity in tagged_activities if activity.title]
