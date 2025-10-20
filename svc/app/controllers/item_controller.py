"""
Item Categorizer Controller and Updated Main Application
"""

# ============================================================================
# FILE: app/controllers/item_controller.py
# ============================================================================

"""
Item categorizer controller endpoints
"""

from typing import Annotated, List, Optional

from fastapi import APIRouter, Body, Depends, Path, Query, status

from svc.app.dal.calendar_repository import CalendarRepository
from svc.app.dal.shopping_repository import ShoppingRepository
from svc.app.dal.todo_repository import TodoRepository
from svc.app.datatypes.calendar import CalendarResponse
from svc.app.datatypes.enums import ItemStatus, ItemType, Priority, ShoppingCategory
from svc.app.datatypes.items import (
    AllItemsResponse,
    ProcessedItemsResponse,
    SuccessResponse,
    UserInputRequest,
)
from svc.app.datatypes.shopping import ShoppingResponse
from svc.app.datatypes.todo import TodoResponse
from svc.app.dependencies import (
    CurrentUser,
    get_calendar_repository,
    get_current_user,
    get_item_categorizer_service,
    get_shopping_repository,
    get_todo_repository,
)
from svc.app.services.smart_item_categorizer_service import ItemCategorizerService
from svc.app.utils.exceptions import ItemNotFoundException

router = APIRouter()


# ============================================================================
# MAIN PROCESSING ENDPOINT
# ============================================================================


@router.post(
    "/process",
    response_model=ProcessedItemsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Process user input",
    description="Parse raw user input and categorize into todos, shopping, and calendar items",
)
async def process_user_input(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    request: UserInputRequest = Body(...),
):
    """
    Process raw text input and automatically categorize items.

    The AI intelligently parses input and extracts:
    - Todo items (tasks, things to do)
    - Shopping items (things to buy)
    - Calendar events (appointments, meetings)
    """
    result = categorizer_service.process_user_input(
        user_id=current_user.id, user_input=request.text
    )

    return ProcessedItemsResponse(
        success=True,
        message="Items processed and saved successfully",
        summary={
            "todos": result["todos_created"],
            "shopping": result["shopping_created"],
            "calendar": result["calendar_created"],
        },
        todos=result["todos"],
        shopping=result["shopping"],
        calendar=result["calendar"],
    )


@router.get(
    "/all",
    response_model=AllItemsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get all active items",
    description="Retrieve all active items for current user",
)
async def get_all_items(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
):
    """Get all active items from the database"""
    items = categorizer_service.get_all_active_items(current_user.id)

    return AllItemsResponse(
        todos=[TodoResponse.model_validate(t) for t in items["todos"]],
        shopping=[ShoppingResponse.model_validate(s) for s in items["shopping"]],
        calendar=[CalendarResponse.model_validate(c) for c in items["calendar"]],
        summaries={
            "todos": {"count": len(items["todos"])},
            "shopping": {"count": len(items["shopping"])},
            "calendar": {"count": len(items["calendar"])},
        },
    )


@router.get(
    "/summary",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get user summary",
    description="Get summary statistics for user's items",
)
async def get_user_summary(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
):
    """Get summary statistics"""
    return categorizer_service.get_user_summary(current_user.id)


# ============================================================================
# TODO ENDPOINTS
# ============================================================================


@router.get(
    "/todos",
    response_model=List[TodoResponse],
    status_code=status.HTTP_200_OK,
    summary="Get todo items",
)
async def get_todos(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    todo_repo: Annotated[TodoRepository, Depends(get_todo_repository)],
    status_filter: Optional[ItemStatus] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get todo items for the current user. Optionally filter by status or priority."""
    if priority:
        todos = todo_repo.get_by_priority(current_user.id, priority, skip, limit)
    elif status_filter == ItemStatus.COMPLETED:
        todos = todo_repo.get_completed_by_user(current_user.id, skip, limit)
    elif status_filter == ItemStatus.PENDING:
        todos = todo_repo.get_active_by_user(current_user.id, skip, limit)
    else:
        todos = todo_repo.get_by_user(current_user.id, skip, limit)

    return [TodoResponse.model_validate(t) for t in todos]


@router.get(
    "/todos/{todo_id}",
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific todo",
)
async def get_todo_by_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    todo_repo: Annotated[TodoRepository, Depends(get_todo_repository)],
    todo_id: int = Path(..., description="Todo ID"),
):
    """Get a specific todo item by ID"""
    todo = todo_repo.get(todo_id)
    if not todo or todo.user_id != current_user.id:
        raise ItemNotFoundException(f"Todo {todo_id} not found")

    return TodoResponse.model_validate(todo)


@router.get(
    "/todos/overdue",
    response_model=List[TodoResponse],
    status_code=status.HTTP_200_OK,
    summary="Get overdue todos",
)
async def get_overdue_todos(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    todo_repo: Annotated[TodoRepository, Depends(get_todo_repository)],
):
    """Get overdue todo items for the current user"""
    todos = todo_repo.get_overdue_by_user(current_user.id)
    return [TodoResponse.model_validate(t) for t in todos]


@router.patch(
    "/todos/{todo_id}/complete",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark todo as complete",
)
async def mark_todo_complete(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    todo_id: int = Path(..., description="Todo ID"),
):
    """Mark a todo item as complete"""
    categorizer_service.mark_todo_complete(current_user.id, todo_id)

    return SuccessResponse(
        success=True, message="Todo marked as complete", item_id=todo_id
    )


@router.delete(
    "/todos/{todo_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete todo",
)
async def delete_todo(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    todo_id: int = Path(..., description="Todo ID"),
):
    """Soft delete a todo item"""
    categorizer_service.delete_item(current_user.id, ItemType.TODO, todo_id)

    return SuccessResponse(
        success=True, message="Todo deleted successfully", item_id=todo_id
    )


# ============================================================================
# SHOPPING ENDPOINTS
# ============================================================================


@router.get(
    "/shopping",
    response_model=List[ShoppingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get shopping items",
)
async def get_shopping(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    shopping_repo: Annotated[ShoppingRepository, Depends(get_shopping_repository)],
    status_filter: Optional[ItemStatus] = Query(None, description="Filter by status"),
    category: Optional[ShoppingCategory] = Query(
        None, description="Filter by category"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get shopping items for the current user. Optionally filter by status or category."""
    if category:
        items = shopping_repo.get_by_category(current_user.id, category, skip, limit)
    elif status_filter == ItemStatus.COMPLETED:
        items = shopping_repo.get_purchased_by_user(current_user.id, skip, limit)
    elif status_filter == ItemStatus.PENDING:
        items = shopping_repo.get_active_by_user(current_user.id, skip, limit)
    else:
        items = shopping_repo.get_by_user(current_user.id, skip, limit)

    return [ShoppingResponse.model_validate(s) for s in items]


@router.get(
    "/shopping/{shopping_id}",
    response_model=ShoppingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific shopping item",
)
async def get_shopping_by_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    shopping_repo: Annotated[ShoppingRepository, Depends(get_shopping_repository)],
    shopping_id: int = Path(..., description="Shopping item ID"),
):
    """Get a specific shopping item by ID"""
    item = shopping_repo.get(shopping_id)
    if not item or item.user_id != current_user.id:
        raise ItemNotFoundException(f"Shopping item {shopping_id} not found")

    return ShoppingResponse.model_validate(item)


@router.patch(
    "/shopping/{shopping_id}/purchase",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark shopping item as purchased",
)
async def mark_shopping_purchased(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    shopping_id: int = Path(..., description="Shopping item ID"),
    actual_price: Optional[float] = Query(None, description="Actual price paid"),
):
    """Mark a shopping item as purchased"""
    categorizer_service.mark_shopping_purchased(
        current_user.id, shopping_id, actual_price
    )

    return SuccessResponse(
        success=True, message="Shopping item marked as purchased", item_id=shopping_id
    )


@router.delete(
    "/shopping/{shopping_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete shopping item",
)
async def delete_shopping(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    shopping_id: int = Path(..., description="Shopping item ID"),
):
    """Soft delete a shopping item"""
    categorizer_service.delete_item(current_user.id, ItemType.SHOPPING, shopping_id)

    return SuccessResponse(
        success=True, message="Shopping item deleted successfully", item_id=shopping_id
    )


# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================


@router.get(
    "/calendar",
    response_model=List[CalendarResponse],
    status_code=status.HTTP_200_OK,
    summary="Get calendar events",
)
async def get_calendar_events(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    calendar_repo: Annotated[CalendarRepository, Depends(get_calendar_repository)],
    upcoming_only: bool = Query(True, description="Only show upcoming events"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    """Get calendar events for the current user. Optionally filter upcoming events."""
    if upcoming_only:
        events = calendar_repo.get_upcoming_by_user(current_user.id, skip, limit)
    else:
        events = calendar_repo.get_by_user(current_user.id, skip, limit)

    return [CalendarResponse.model_validate(e) for e in events]


@router.get(
    "/calendar/today",
    response_model=List[CalendarResponse],
    status_code=status.HTTP_200_OK,
    summary="Get today's events",
)
async def get_today_events(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    calendar_repo: Annotated[CalendarRepository, Depends(get_calendar_repository)],
):
    """Get today's calendar events for the current user"""
    events = calendar_repo.get_today_by_user(current_user.id)
    return [CalendarResponse.model_validate(e) for e in events]


@router.get(
    "/calendar/{event_id}",
    response_model=CalendarResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific calendar event",
)
async def get_calendar_by_id(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    calendar_repo: Annotated[CalendarRepository, Depends(get_calendar_repository)],
    event_id: int = Path(..., description="Calendar event ID"),
):
    """Get a specific calendar event by ID"""
    event = calendar_repo.get(event_id)
    if not event or event.user_id != current_user.id:
        raise ItemNotFoundException(f"Calendar event {event_id} not found")

    return CalendarResponse.model_validate(event)


@router.patch(
    "/calendar/{event_id}/complete",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark calendar event as complete",
)
async def mark_calendar_completed(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    event_id: int = Path(..., description="Calendar event ID"),
):
    """Mark a calendar event as completed"""
    categorizer_service.mark_calendar_completed(current_user.id, event_id)

    return SuccessResponse(
        success=True, message="Calendar event marked as complete", item_id=event_id
    )


@router.delete(
    "/calendar/{event_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete calendar event",
)
async def delete_calendar(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    categorizer_service: Annotated[
        ItemCategorizerService, Depends(get_item_categorizer_service)
    ],
    event_id: int = Path(..., description="Calendar event ID"),
):
    """Soft delete a calendar event"""
    categorizer_service.delete_item(current_user.id, ItemType.CALENDAR, event_id)

    return SuccessResponse(
        success=True, message="Calendar event deleted successfully", item_id=event_id
    )
