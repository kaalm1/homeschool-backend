import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from svc.app.dal.calendar_repository import CalendarRepository
from svc.app.dal.shopping_repository import ShoppingRepository
from svc.app.dal.todo_repository import TodoRepository
from svc.app.datatypes.calendar import CalendarResponse, ParsedCalendar
from svc.app.datatypes.enums import ItemType, Priority, ShoppingCategory
from svc.app.datatypes.shopping import ParsedShopping, ShoppingResponse
from svc.app.datatypes.todo import ParsedTodo, TodoResponse
from svc.app.models.calendar_event import CalendarEvent
from svc.app.models.shopping_item import ShoppingItem
from svc.app.models.todo_item import TodoItem
from svc.app.services.item_parser_service import ItemParserService
from svc.app.utils.exceptions import ItemNotFoundException, ParsingException

logger = logging.getLogger(__name__)


class ItemCategorizerService:
    """Main service that orchestrates parsing and database operations"""

    def __init__(
        self,
        todo_repository: TodoRepository,
        shopping_repository: ShoppingRepository,
        calendar_repository: CalendarRepository,
        parser_service: ItemParserService,
    ):
        """
        Initialize the service

        Args:
            todo_repository: Todo repository instance
            shopping_repository: Shopping repository instance
            calendar_repository: Calendar repository instance
            parser_service: Parser service instance
        """
        self.todo_repo = todo_repository
        self.shopping_repo = shopping_repository
        self.calendar_repo = calendar_repository
        self.parser_service = parser_service

        logger.info("ItemCategorizerService initialized")

    def process_user_input(self, user_id: int, user_input: str) -> Dict[str, Any]:
        """
        Process raw user input, parse it, and save to database.

        Args:
            user_id: User ID
            user_input: Raw text from user

        Returns:
            Dictionary with summary of created items

        Raises:
            ParsingException: If parsing fails
        """
        logger.info(f"Processing input for user {user_id}: {user_input[:50]}...")

        try:
            # Parse input using AI
            parsed_result = self.parser_service.parse_user_input(user_input)

            # Save todos
            saved_todos = []
            for parsed_todo in parsed_result.todos:
                todo = self._save_todo(user_id, parsed_todo)
                saved_todos.append(todo)

            # Save shopping items
            saved_shopping = []
            for parsed_shopping in parsed_result.shopping:
                item = self._save_shopping(user_id, parsed_shopping)
                saved_shopping.append(item)

            # Save calendar events
            saved_calendar = []
            for parsed_calendar in parsed_result.calendar:
                event = self._save_calendar(user_id, parsed_calendar)
                saved_calendar.append(event)

            logger.info(
                f"Successfully processed {len(saved_todos)} todos, "
                f"{len(saved_shopping)} shopping items, "
                f"{len(saved_calendar)} calendar events for user {user_id}"
            )

            return {
                "todos_created": len(saved_todos),
                "shopping_created": len(saved_shopping),
                "calendar_created": len(saved_calendar),
                "todos": [TodoResponse.model_validate(t) for t in saved_todos],
                "shopping": [
                    ShoppingResponse.model_validate(s) for s in saved_shopping
                ],
                "calendar": [
                    CalendarResponse.model_validate(c) for c in saved_calendar
                ],
            }

        except Exception as e:
            logger.error(f"Failed to process input for user {user_id}: {str(e)}")
            raise ParsingException(f"Failed to process input: {str(e)}")

    def _save_todo(self, user_id: int, parsed_todo: ParsedTodo) -> TodoItem:
        """Save a todo item to database"""
        due_date = None
        if parsed_todo.due_date:
            try:
                due_date = datetime.fromisoformat(parsed_todo.due_date)
            except (ValueError, TypeError):
                logger.warning(f"Invalid due_date format: {parsed_todo.due_date}")

        # Convert string priority to enum
        priority = None
        if parsed_todo.priority:
            try:
                priority = Priority(parsed_todo.priority.lower())
            except ValueError:
                logger.warning(f"Invalid priority: {parsed_todo.priority}")

        return self.todo_repo.create_todo(
            user_id=user_id,
            title=parsed_todo.title,
            description=parsed_todo.description,
            priority=priority,
            due_date=due_date,
            estimated_hours=parsed_todo.estimated_hours,
            tags=parsed_todo.tags,
        )

    def _save_shopping(
        self, user_id: int, parsed_shopping: ParsedShopping
    ) -> ShoppingItem:
        """Save a shopping item to database"""
        # Convert string category to enum
        category = None
        if parsed_shopping.category:
            try:
                category = ShoppingCategory(parsed_shopping.category.lower())
            except ValueError:
                logger.warning(f"Invalid category: {parsed_shopping.category}")
                category = ShoppingCategory.OTHER

        # Parse estimated price
        estimated_price = None
        if parsed_shopping.estimated_price:
            try:
                # Remove currency symbols and convert to float
                price_str = parsed_shopping.estimated_price.replace("$", "").strip()
                estimated_price = float(price_str)
            except (ValueError, TypeError):
                logger.warning(f"Invalid price: {parsed_shopping.estimated_price}")

        return self.shopping_repo.create_shopping_item(
            user_id=user_id,
            item_name=parsed_shopping.item_name,
            quantity=parsed_shopping.quantity,
            category=category,
            notes=parsed_shopping.notes,
            estimated_price=estimated_price,
            store_name=parsed_shopping.store_name,
            priority=parsed_shopping.priority or 0,
        )

    def _save_calendar(
        self, user_id: int, parsed_calendar: ParsedCalendar
    ) -> CalendarEvent:
        """Save a calendar event to database"""
        start_time = datetime.fromisoformat(parsed_calendar.start_time)
        end_time = None
        if parsed_calendar.end_time:
            try:
                end_time = datetime.fromisoformat(parsed_calendar.end_time)
            except (ValueError, TypeError):
                logger.warning(f"Invalid end_time: {parsed_calendar.end_time}")

        return self.calendar_repo.create_event(
            user_id=user_id,
            title=parsed_calendar.title,
            description=parsed_calendar.description,
            location=parsed_calendar.location,
            start_time=start_time,
            end_time=end_time,
            all_day=parsed_calendar.all_day,
            reminder_minutes=parsed_calendar.reminder_minutes,
            url=parsed_calendar.url,
            attendees=parsed_calendar.attendees,
        )

    def get_all_active_items(self, user_id: int) -> Dict[str, List]:
        """
        Get all active items from database for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary with todos, shopping, and calendar lists
        """
        logger.info(f"Getting all active items for user {user_id}")

        return {
            "todos": self.todo_repo.get_active_by_user(user_id),
            "shopping": self.shopping_repo.get_active_by_user(user_id),
            "calendar": self.calendar_repo.get_upcoming_by_user(user_id),
        }

    def mark_todo_complete(self, user_id: int, todo_id: int) -> Optional[TodoItem]:
        """
        Mark a todo as complete

        Args:
            user_id: User ID
            todo_id: Todo ID

        Returns:
            Updated TodoItem or None if not found

        Raises:
            ItemNotFoundException: If todo not found or doesn't belong to user
        """
        todo = self.todo_repo.get(todo_id)
        if not todo or todo.user_id != user_id:
            raise ItemNotFoundException(f"Todo {todo_id} not found for user {user_id}")

        logger.info(f"Marking todo {todo_id} as complete for user {user_id}")
        return self.todo_repo.mark_complete(todo_id)

    def mark_shopping_purchased(
        self, user_id: int, shopping_id: int, actual_price: Optional[float] = None
    ) -> Optional[ShoppingItem]:
        """
        Mark a shopping item as purchased

        Args:
            user_id: User ID
            shopping_id: Shopping item ID
            actual_price: Optional actual price paid

        Returns:
            Updated ShoppingItem or None if not found

        Raises:
            ItemNotFoundException: If item not found or doesn't belong to user
        """
        item = self.shopping_repo.get(shopping_id)
        if not item or item.user_id != user_id:
            raise ItemNotFoundException(
                f"Shopping item {shopping_id} not found for user {user_id}"
            )

        logger.info(
            f"Marking shopping item {shopping_id} as purchased for user {user_id}"
        )
        return self.shopping_repo.mark_purchased(shopping_id, actual_price)

    def mark_calendar_completed(
        self, user_id: int, event_id: int
    ) -> Optional[CalendarEvent]:
        """
        Mark a calendar event as completed

        Args:
            user_id: User ID
            event_id: Calendar event ID

        Returns:
            Updated CalendarEvent or None if not found

        Raises:
            ItemNotFoundException: If event not found or doesn't belong to user
        """
        event = self.calendar_repo.get(event_id)
        if not event or event.user_id != user_id:
            raise ItemNotFoundException(
                f"Calendar event {event_id} not found for user {user_id}"
            )

        logger.info(
            f"Marking calendar event {event_id} as completed for user {user_id}"
        )
        return self.calendar_repo.mark_completed(event_id)

    def delete_item(self, user_id: int, item_type: ItemType, item_id: int) -> bool:
        """
        Delete an item (soft delete)

        Args:
            user_id: User ID
            item_type: Type of item to delete
            item_id: Item ID

        Returns:
            True if deleted, False if not found

        Raises:
            ItemNotFoundException: If item not found or doesn't belong to user
        """
        logger.info(f"Deleting {item_type.value} {item_id} for user {user_id}")

        if item_type == ItemType.TODO:
            todo = self.todo_repo.get(item_id)
            if not todo or todo.user_id != user_id:
                raise ItemNotFoundException(
                    f"Todo {item_id} not found for user {user_id}"
                )
            self.todo_repo.mark_deleted(item_id)
            return True

        elif item_type == ItemType.SHOPPING:
            item = self.shopping_repo.get(item_id)
            if not item or item.user_id != user_id:
                raise ItemNotFoundException(
                    f"Shopping item {item_id} not found for user {user_id}"
                )
            self.shopping_repo.mark_deleted(item_id)
            return True

        elif item_type == ItemType.CALENDAR:
            event = self.calendar_repo.get(item_id)
            if not event or event.user_id != user_id:
                raise ItemNotFoundException(
                    f"Calendar event {item_id} not found for user {user_id}"
                )
            self.calendar_repo.mark_deleted(item_id)
            return True

        return False

    def get_user_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Get summary statistics for user's items

        Args:
            user_id: User ID

        Returns:
            Dictionary with counts and statistics
        """
        logger.info(f"Getting summary for user {user_id}")

        # Todo stats
        active_todos = self.todo_repo.count_active_by_user(user_id)
        overdue_todos = len(self.todo_repo.get_overdue_by_user(user_id))

        # Shopping stats
        active_shopping = len(self.shopping_repo.get_active_by_user(user_id))
        total_estimated_cost = self.shopping_repo.get_total_estimated_cost(user_id)

        # Calendar stats
        upcoming_events = self.calendar_repo.count_upcoming_by_user(user_id)
        today_events = len(self.calendar_repo.get_today_by_user(user_id))

        return {
            "todos": {"active": active_todos, "overdue": overdue_todos},
            "shopping": {
                "active": active_shopping,
                "total_estimated_cost": total_estimated_cost,
            },
            "calendar": {"upcoming": upcoming_events, "today": today_events},
        }
