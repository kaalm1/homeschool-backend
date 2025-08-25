from typing import Annotated
from fastapi import APIRouter, Depends, status

from ..services.auth_service import AuthService
from ..datatypes.auth import LoginRequest, RegisterRequest, TokenResponse
from ..datatypes.user import UserResponse
from ..dependencies import get_auth_service, CurrentUser

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    login_data: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Authenticate user and return access token."""
    return auth_service.login(login_data)


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    register_data: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Register new user and return access token."""
    return auth_service.register(register_data)


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user information."""
    return UserResponse.model_validate(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout():
    """Logout user (client-side token removal)."""
    return {"success": True, "message": "Successfully logged out"}
