from datetime import date, timedelta
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query

from svc.app.datatypes.week_activity import (
    BulkWeekActivityCreate,
    PlanWeekActivityRequest,
    WeekActivityCreate,
    WeekActivityResponse,
    WeekActivityUpdate,
    WeekSummary,
)
from svc.app.dependencies import (
    CurrentUser,
    get_current_user,
    get_enhanced_activity_planner_service,
    get_week_activity_service,
)
from svc.app.services.enhanced_activity_planner_service import (
    EnhancedActivityPlannerService,
)
from svc.app.services.week_activity_service import WeekActivityService

router = APIRouter()


@router.post(
    "/week-activities/plan-week",
    response_model=List[WeekActivityResponse],
    status_code=201,
)
async def plan_week_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    request: PlanWeekActivityRequest,
    planner_service: EnhancedActivityPlannerService = Depends(
        get_enhanced_activity_planner_service
    ),
    week_service: WeekActivityService = Depends(get_week_activity_service),
):
    """Plan activities for a week using AI recommendations and create week activity assignments."""
    target_week_start = request.target_week_start
    # Determine the target week if not provided
    if target_week_start is None:
        target_week_start = date.today()
        # Adjust to start of week (Monday)
        days_since_monday = target_week_start.weekday()
        target_week_start = target_week_start - timedelta(days=days_since_monday)

    # Get AI-generated activity recommendations
    planned_activities = await planner_service.plan_weekly_activities(
        user_id=current_user.id,
        target_week=target_week_start,
        additional_notes=request.additional_notes,
    )

    if not planned_activities:
        return []

    # Convert planned activities to week activity assignments
    year, week, _ = target_week_start.isocalendar()

    # Create WeekActivityCreate objects from the planned activities
    week_activity_assignments = []
    for activity in planned_activities:
        assignment = WeekActivityCreate(
            activity_id=activity["id"],
            activity_year=year,
            activity_week=week,
            llm_suggestion=True,
        )
        week_activity_assignments.append(assignment)

    # Bulk create the week activities
    bulk_data = BulkWeekActivityCreate(assignments=week_activity_assignments)

    try:
        created_activities = week_service.bulk_create_week_activities(
            current_user.id, bulk_data
        )

        # Enhance the response with the AI planning reasoning
        for i, created_activity in enumerate(created_activities):
            if i < len(planned_activities):
                # Add the AI reasoning to the notes if no notes exist
                if not created_activity.notes and planned_activities[i].get(
                    "why_it_fits"
                ):
                    # Update with the planning reason
                    update_data = WeekActivityUpdate(
                        llm_notes=f"AI Recommended: {planned_activities[i]['why_it_fits']}"
                    )
                    created_activities[i] = week_service.update_week_activity(
                        created_activity.id, update_data
                    )

        return created_activities

    except Exception as e:
        # If bulk creation fails, try individual creation to handle conflicts gracefully
        successfully_created = []
        for assignment in week_activity_assignments:
            try:
                created = week_service.create_week_activity(current_user.id, assignment)
                successfully_created.append(created)
            except Exception:
                # Skip activities that couldn't be created (e.g., already exist)
                continue

        return successfully_created


@router.post("/week-activities", response_model=WeekActivityResponse, status_code=201)
def create_week_activity(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    week_activity: WeekActivityCreate,
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Create a new week activity assignment."""
    return service.create_week_activity(current_user.id, week_activity)


@router.put("/week-activities/{week_activity_id}", response_model=WeekActivityResponse)
def update_week_activity(
    week_activity_id: int,
    update_data: WeekActivityUpdate,
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Update a week activity's completion status, rating, and notes."""
    return service.update_week_activity(week_activity_id, update_data)


@router.post(
    "/week-activities/{week_activity_id}/toggle", response_model=WeekActivityResponse
)
def toggle_week_activity(
    week_activity_id: int,
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Toggle the completion status of a week activity."""
    return service.toggle_week_activity(week_activity_id)


@router.post(
    "/week-activities/bulk", response_model=List[WeekActivityResponse], status_code=201
)
def bulk_create_week_activities(
    bulk_data: BulkWeekActivityCreate,
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Create multiple week activity assignments at once."""
    return service.bulk_create_week_activities(bulk_data)


@router.get("/week-activities/current", response_model=List[WeekActivityResponse])
def get_current_week_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Get activities for the current week."""
    return service.get_current_week_activities(user_id=current_user.id)


@router.get("/week-activities", response_model=List[WeekActivityResponse])
def get_week_activities(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    year: Optional[int] = Query(None, description="Year to filter by"),
    week: Optional[int] = Query(None, description="Week number to filter by (1-53)"),
    completed_only: Optional[bool] = Query(
        None, description="Filter by completion status"
    ),
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Get week activities with optional filters."""
    return service.get_week_activities(
        year=year, week=week, user_id=current_user.id, completed_only=completed_only
    )


@router.get("/week-activities/summary", response_model=WeekSummary)
def get_week_summary(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    week: Optional[int] = Query(
        None, description="Week number (defaults to current week)"
    ),
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Get a summary of activities for a specific week with completion stats."""
    return service.get_week_summary(year=year, week=week, user_id=current_user.id)


@router.get("/week-activities/weeks", response_model=List[dict])
def get_available_weeks(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Get all weeks that have activities."""
    return service.get_available_weeks(user_id=current_user.id)


@router.delete("/week-activities/{week_activity_id}", status_code=204)
def delete_week_activity(
    week_activity_id: int,
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Delete a week activity assignment by ID."""
    service.delete_week_activity(week_activity_id)


@router.delete("/week-activities/remove", status_code=204)
def remove_activity_from_week(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    activity_id: int = Query(..., description="Activity ID"),
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    week: Optional[int] = Query(
        None, description="Week number (defaults to current week)"
    ),
    service: WeekActivityService = Depends(get_week_activity_service),
):
    """Remove a specific activity from a user's week."""
    service.remove_activity_from_week(
        user_id=current_user.id, activity_id=activity_id, year=year, week=week
    )
