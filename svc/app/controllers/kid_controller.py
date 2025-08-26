from typing import Annotated, List

from fastapi import APIRouter, Depends, status

from ..datatypes.kid import KidCreate, KidResponse, KidUpdate
from ..dependencies import CurrentUser, get_kid_service
from ..services.kid_service import KidService

router = APIRouter()


@router.get("", response_model=List[KidResponse], status_code=status.HTTP_200_OK)
async def get_kids(
    current_user: CurrentUser,
    kid_service: Annotated[KidService, Depends(get_kid_service)],
):
    """Get all kids for the current user."""
    return kid_service.get_kids_by_parent(current_user.id)


@router.post("", response_model=KidResponse, status_code=status.HTTP_201_CREATED)
async def create_kid(
    kid_data: KidCreate,
    current_user: CurrentUser,
    kid_service: Annotated[KidService, Depends(get_kid_service)],
):
    """Create a new kid."""
    return kid_service.create_kid(kid_data, current_user.id)


@router.get("/{kid_id}", response_model=KidResponse, status_code=status.HTTP_200_OK)
async def get_kid(
    kid_id: int,
    current_user: CurrentUser,
    kid_service: Annotated[KidService, Depends(get_kid_service)],
):
    """Get a specific kid by ID."""
    return kid_service.get_kid_by_id(kid_id, current_user.id)


@router.patch("/{kid_id}", response_model=KidResponse, status_code=status.HTTP_200_OK)
async def update_kid(
    kid_id: int,
    kid_data: KidUpdate,
    current_user: CurrentUser,
    kid_service: Annotated[KidService, Depends(get_kid_service)],
):
    """Update a kid's information."""
    return kid_service.update_kid(kid_id, kid_data, current_user.id)


@router.delete("/{kid_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kid(
    kid_id: int,
    current_user: CurrentUser,
    kid_service: Annotated[KidService, Depends(get_kid_service)],
):
    """Delete a kid."""
    kid_service.delete_kid(kid_id, current_user.id)
    return None
