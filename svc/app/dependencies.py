import os
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from openai import OpenAI
from sqlalchemy.orm import Session

from svc.app.dal.activity_repository import ActivityRepository
from svc.app.dal.activity_suggestion_repository import ActivitySuggestionRepository
from svc.app.dal.family_preference_repository import FamilyPreferenceRepository
from svc.app.dal.kid_repository import KidRepository
from svc.app.dal.user_behavior_analytic_repository import (
    UserBehaviorAnalyticsRepository,
)
from svc.app.dal.user_repository import UserRepository
from svc.app.dal.week_activity_repository import WeekActivityRepository
from svc.app.database import get_db_session
from svc.app.llm.client import llm_client
from svc.app.llm.services.planner_service import ActivityPlannerService
from svc.app.models.user import User
from svc.app.services.activity_service import ActivityService
from svc.app.services.activity_suggestion_service import HistoricalActivityAnalyzer
from svc.app.services.auth_service import AuthService
from svc.app.services.behavior_analytics_service import BehaviorAnalyticsService
from svc.app.services.enhanced_activity_planner_service import (
    EnhancedActivityPlannerService,
)
from svc.app.services.family_preference_service import FamilyPreferenceService
from svc.app.services.family_profile_service import FamilyProfileService
from svc.app.services.kid_service import KidService
from svc.app.services.settings_service import SettingsService
from svc.app.services.user_seeding_service import UserSeedingService
from svc.app.services.user_service import UserService
from svc.app.services.weather_service import WeatherService
from svc.app.services.week_activity_service import WeekActivityService

security = HTTPBearer(auto_error=True)

# Database dependency
DatabaseSession = Annotated[Session, Depends(get_db_session)]


def get_openai_client():
    """Get configured OpenAI client."""
    return llm_client


# Repository dependencies
def get_user_repository(db: DatabaseSession) -> UserRepository:
    return UserRepository(db)


def get_kid_repository(db: DatabaseSession) -> KidRepository:
    return KidRepository(db)


def get_activity_repository(db: DatabaseSession) -> ActivityRepository:
    return ActivityRepository(db)


def get_week_activity_repository(db: DatabaseSession) -> WeekActivityRepository:
    return WeekActivityRepository(db)


def get_family_preference_repository(db: DatabaseSession) -> FamilyPreferenceRepository:
    return FamilyPreferenceRepository(db)


def get_activity_suggestion_repository(
    db: DatabaseSession,
) -> ActivitySuggestionRepository:
    return ActivitySuggestionRepository(db)


def get_user_behaviour_anlaytics_repository(
    db: DatabaseSession,
) -> UserBehaviorAnalyticsRepository:
    return UserBehaviorAnalyticsRepository(db)


def get_user_seeding_service(
    activity_repo: Annotated[ActivityRepository, Depends(get_activity_repository)],
) -> UserSeedingService:
    return UserSeedingService(activity_repo)


# Service dependencies
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    user_seeding_service: Annotated[
        UserSeedingService, Depends(get_user_seeding_service)
    ],
) -> AuthService:
    return AuthService(user_repo, user_seeding_service)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> UserService:
    return UserService(user_repo)


def get_kid_service(
    kid_repo: Annotated[KidRepository, Depends(get_kid_repository)]
) -> KidService:
    return KidService(kid_repo)


def get_activity_service(
    activity_repo: Annotated[ActivityRepository, Depends(get_activity_repository)],
    kid_repo: Annotated[KidRepository, Depends(get_kid_repository)],
) -> ActivityService:
    return ActivityService(activity_repo, kid_repo)


def get_week_activity_service(
    week_activity_repo: Annotated[
        WeekActivityRepository, Depends(get_week_activity_repository)
    ],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    activity_repo: Annotated[ActivityRepository, Depends(get_activity_repository)],
) -> WeekActivityService:
    return WeekActivityService(week_activity_repo, user_repo, activity_repo)


def get_activity_planner_service(
    activity_service: Annotated[ActivityService, Depends(get_activity_service)],
    kid_service: Annotated[KidService, Depends(get_kid_service)],
) -> ActivityPlannerService:
    return ActivityPlannerService(activity_service, kid_service)


def get_behaviour_analytics_service(
    analytics_repo: Annotated[
        UserBehaviorAnalyticsRepository,
        Depends(get_user_behaviour_anlaytics_repository),
    ],
    suggestion_repo: Annotated[
        ActivitySuggestionRepository, Depends(get_activity_suggestion_repository)
    ],
) -> BehaviorAnalyticsService:
    return BehaviorAnalyticsService(analytics_repo, suggestion_repo)


def get_historical_activity_analyzer(
    activity_suggestion_repo: Annotated[
        ActivitySuggestionRepository, Depends(get_activity_suggestion_repository)
    ],
    behaviour_analytics_service: Annotated[
        BehaviorAnalyticsService, Depends(get_behaviour_analytics_service)
    ],
) -> HistoricalActivityAnalyzer:
    return HistoricalActivityAnalyzer(
        activity_suggestion_repo, behaviour_analytics_service
    )


def get_weather_service() -> WeatherService:
    return WeatherService()


def get_settings_service() -> SettingsService:
    """Get settings service dependency."""
    return SettingsService()


def get_family_preference_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    family_preference_repo: Annotated[
        FamilyPreferenceRepository, Depends(get_family_preference_repository)
    ],
) -> FamilyPreferenceService:
    """Dependency to get family preference service."""
    return FamilyPreferenceService(family_preference_repo, user_repo)


def get_family_profile_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    kid_service: Annotated[KidService, Depends(get_kid_service)],
    family_preference_service: Annotated[
        FamilyPreferenceService, Depends(get_family_preference_service)
    ],
) -> FamilyProfileService:
    return FamilyProfileService(user_repo, kid_service, family_preference_service)


def get_enhanced_activity_planner_service(
    family_profile_service: Annotated[
        FamilyProfileService, Depends(get_family_profile_service)
    ],
    activity_repo: Annotated[ActivityRepository, Depends(get_activity_repository)],
    suggestion_repo: Annotated[
        ActivitySuggestionRepository, Depends(get_activity_suggestion_repository)
    ],
    week_activity_repo: Annotated[
        WeekActivityRepository, Depends(get_week_activity_repository)
    ],
    historical_analyzer: Annotated[
        HistoricalActivityAnalyzer, Depends(get_historical_activity_analyzer)
    ],
    weather_service: Annotated[WeatherService, Depends(get_weather_service)],
    openai_client: Annotated[OpenAI, Depends(get_openai_client)],
) -> EnhancedActivityPlannerService:
    return EnhancedActivityPlannerService(
        family_profile_service=family_profile_service,
        activity_repo=activity_repo,
        suggestion_repo=suggestion_repo,
        week_activity_repo=week_activity_repo,
        historical_analyzer=historical_analyzer,
        weather_service=weather_service,
        llm_client=openai_client,
    )


# Authentication dependency
def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    return auth_service.get_current_user_from_token(credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]
