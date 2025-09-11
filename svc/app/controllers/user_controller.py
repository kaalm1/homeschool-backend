from typing import Annotated

from fastapi import APIRouter, Depends, status

from svc.app.datatypes.user import UserResponse, UserUpdate
from svc.app.dependencies import CurrentUser, get_user_service
from svc.app.services.user_service import UserService

router = APIRouter(tags=["users"])


@router.get("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user_profile(
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Get current user's profile information."""
    return user_service.get_user_profile(current_user.id)


@router.get("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Get a specific user by ID."""
    return user_service.get_user_profile(user_id)


@router.patch("/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Update user information."""
    return user_service.update_user(user_id, user_data)


@router.patch("/profile", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Update current user's profile information."""
    return user_service.update_user(current_user.id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    current_user: CurrentUser,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """Deactivate user account."""
    user_service.deactivate_user(user_id)
    return None
