from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .dal.activity_repository import ActivityRepository
from .dal.kid_repository import KidRepository
from .dal.user_repository import UserRepository
from .dal.week_activity_repository import WeekActivityRepository
from .database import get_db_session
from .models.user import User
from .services.activity_service import ActivityService
from .services.auth_service import AuthService
from .services.kid_service import KidService
from .services.user_service import UserService
from .services.week_activity_service import WeekActivityService

security = HTTPBearer(auto_error=True)

# Database dependency
DatabaseSession = Annotated[Session, Depends(get_db_session)]


# Repository dependencies
def get_user_repository(db: DatabaseSession) -> UserRepository:
    return UserRepository(db)


def get_kid_repository(db: DatabaseSession) -> KidRepository:
    return KidRepository(db)


def get_activity_repository(db: DatabaseSession) -> ActivityRepository:
    return ActivityRepository(db)


def get_week_activity_repository(db: DatabaseSession) -> WeekActivityRepository:
    return WeekActivityRepository(db)


# Service dependencies
def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)]
) -> AuthService:
    return AuthService(user_repo)


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


# Authentication dependency
def get_current_user(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    return auth_service.get_current_user_from_token(credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]
