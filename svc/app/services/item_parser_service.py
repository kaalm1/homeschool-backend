"""
Item Parser Service with Strict JSON Schema
"""

# ============================================================================
# FILE: app/services/parser_service.py
# ============================================================================

"""
AI parsing service using Claude with strict JSON schema
"""

import json
import logging
from datetime import datetime
from typing import Optional

from svc.app.config import settings
from svc.app.datatypes.calendar import ParsedCalendar
from svc.app.datatypes.items import ParsedResult
from svc.app.datatypes.shopping import ParsedShopping
from svc.app.datatypes.todo import ParsedTodo

# Import your LLM client
from svc.app.llm.client import llm_client
from svc.app.utils.exceptions import ParsingException

logger = logging.getLogger(__name__)


class ParserService:
    """Service for parsing user input using Claude AI with strict JSON schema"""

    # Strict JSON schema for structured output
    JSON_SCHEMA = {
        "type": "object",
        "properties": {
            "todos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Todo title"},
                        "description": {
                            "type": ["string", "null"],
                            "description": "Todo description",
                        },
                        "priority": {
                            "type": ["string", "null"],
                            "enum": ["high", "medium", "low", None],
                            "description": "Priority level",
                        },
                        "due_date": {
                            "type": ["string", "null"],
                            "description": "Due date in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                        },
                        "estimated_hours": {
                            "type": ["number", "null"],
                            "description": "Estimated hours to complete",
                        },
                        "tags": {
                            "type": ["string", "null"],
                            "description": "Comma-separated tags",
                        },
                    },
                    "required": ["title"],
                    "additionalProperties": False,
                },
            },
            "shopping": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item_name": {"type": "string", "description": "Item name"},
                        "quantity": {
                            "type": ["string", "null"],
                            "description": "Quantity (e.g., '2 lbs', '1 box')",
                        },
                        "category": {
                            "type": ["string", "null"],
                            "enum": [
                                "groceries",
                                "electronics",
                                "clothing",
                                "household",
                                "health",
                                "entertainment",
                                "other",
                                None,
                            ],
                            "description": "Shopping category",
                        },
                        "notes": {
                            "type": ["string", "null"],
                            "description": "Additional notes",
                        },
                        "estimated_price": {
                            "type": ["string", "null"],
                            "description": "Estimated price as string (e.g., '$5.99')",
                        },
                        "store_name": {
                            "type": ["string", "null"],
                            "description": "Store name",
                        },
                        "priority": {
                            "type": ["integer", "null"],
                            "minimum": 0,
                            "maximum": 10,
                            "description": "Priority from 0-10",
                        },
                    },
                    "required": ["item_name"],
                    "additionalProperties": False,
                },
            },
            "calendar": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Event title"},
                        "description": {
                            "type": ["string", "null"],
                            "description": "Event description",
                        },
                        "location": {
                            "type": ["string", "null"],
                            "description": "Event location",
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                        },
                        "end_time": {
                            "type": ["string", "null"],
                            "description": "End time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)",
                        },
                        "all_day": {
                            "type": "boolean",
                            "description": "Whether this is an all-day event",
                        },
                        "reminder_minutes": {
                            "type": ["integer", "null"],
                            "minimum": 0,
                            "description": "Minutes before event to send reminder",
                        },
                        "url": {
                            "type": ["string", "null"],
                            "description": "Meeting URL if applicable",
                        },
                        "attendees": {
                            "type": ["string", "null"],
                            "description": "Comma-separated list of attendees",
                        },
                    },
                    "required": ["title", "start_time"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["todos", "shopping", "calendar"],
        "additionalProperties": False,
    }

    def __init__(self):
        """
        Initialize the parser service with Anthropic API key
        """
        self.client = llm_client

    def parse_user_input(self, user_input: str) -> ParsedResult:
        """
        Parse raw user input and categorize into todos, shopping, and calendar items.

        Args:
            user_input: Raw text from user containing mixed items

        Returns:
            ParsedResult containing categorized items

        Raises:
            ParsingException: If parsing fails
        """
        logger.info(f"Parsing user input: {user_input[:100]}...")

        current_time = datetime.utcnow().isoformat()

        system_prompt = """You are a smart assistant that categorizes user input into three types:
1. TODO items - tasks, things to do, reminders, deadlines
2. SHOPPING items - things to buy, groceries, items to purchase
3. CALENDAR events - appointments, meetings, scheduled events with specific times

Your task is to analyze user input and extract all items, categorizing each appropriately.

IMPORTANT RULES:
- Use ISO 8601 format for all dates/times: YYYY-MM-DDTHH:MM:SS
- Infer reasonable values when possible (e.g., "tomorrow at 2pm" should calculate actual datetime)
- For todos without specific dates, set due_date to null
- For shopping items, try to categorize into: groceries, electronics, clothing, household, health, entertainment, or other
- Parse prices carefully (remove currency symbols if present)
- Default priority for todos: null (only set if explicitly mentioned)
- Default all_day for calendar: false (unless explicitly stated)
- Set reasonable reminder times (e.g., 30 minutes for appointments)"""

        user_prompt = f"""Current datetime for reference: {current_time}

User input to parse:
{user_input}

Analyze the above input and extract all todos, shopping items, and calendar events."""

        try:
            # Use Claude's structured outputs with JSON schema
            message = self.client.messages.create(
                model=settings.llm_model,
                max_tokens=4000,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                # Enable structured outputs with JSON schema
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "item_categorization",
                        "strict": True,
                        "schema": self.JSON_SCHEMA,
                    },
                },
            )

            # Extract the JSON response
            response_text = message.content[0].text.strip()

            # Parse JSON response
            data = json.loads(response_text)

            logger.info(
                f"Parsed {len(data.get('todos', []))} todos, "
                f"{len(data.get('shopping', []))} shopping items, "
                f"{len(data.get('calendar', []))} calendar events"
            )

            # Convert to Pydantic models
            todos = [ParsedTodo(**item) for item in data.get("todos", [])]
            shopping = [ParsedShopping(**item) for item in data.get("shopping", [])]
            calendar = [ParsedCalendar(**item) for item in data.get("calendar", [])]

            return ParsedResult(todos=todos, shopping=shopping, calendar=calendar)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise ParsingException(f"Failed to parse JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise ParsingException(f"Failed to parse user input: {str(e)}")

    def validate_schema(self) -> bool:
        """
        Validate that the JSON schema is properly formatted

        Returns:
            True if schema is valid
        """
        try:
            # Basic validation - check required fields
            assert "type" in self.JSON_SCHEMA
            assert "properties" in self.JSON_SCHEMA
            assert "todos" in self.JSON_SCHEMA["properties"]
            assert "shopping" in self.JSON_SCHEMA["properties"]
            assert "calendar" in self.JSON_SCHEMA["properties"]
            logger.info("JSON schema validation passed")
            return True
        except AssertionError as e:
            logger.error(f"JSON schema validation failed: {str(e)}")
            return False


# ============================================================================
# ALTERNATIVE: Fallback parser without structured outputs
# ============================================================================


class FallbackParserService:
    """
    Fallback parser service that uses traditional prompt engineering
    (in case structured outputs are not available)
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the fallback parser service"""
        self.client = llm_client

    def parse_user_input(self, user_input: str) -> ParsedResult:
        """
        Parse raw user input using traditional prompt engineering

        Args:
            user_input: Raw text from user

        Returns:
            ParsedResult containing categorized items
        """
        current_time = datetime.utcnow().isoformat()

        prompt = f"""You are a smart assistant that categorizes user input into three types:
1. TODO items - tasks, things to do, reminders
2. SHOPPING items - things to buy, groceries, items to purchase
3. CALENDAR events - appointments, meetings, scheduled events

Analyze the following user input and extract all items, categorizing each one appropriately.

User input: {user_input}

Current datetime for reference: {current_time}

Respond ONLY with valid JSON in this EXACT format (no markdown, no extra text, no code blocks):
{{
  "todos": [
    {{
      "title": "string (required)",
      "description": "string or null",
      "priority": "high/medium/low or null",
      "due_date": "ISO 8601 datetime string or null",
      "estimated_hours": number or null,
      "tags": "string or null"
    }}
  ],
  "shopping": [
    {{
      "item_name": "string (required)",
      "quantity": "string or null",
      "category": "groceries/electronics/clothing/household/health/entertainment/other or null",
      "notes": "string or null",
      "estimated_price": "string or null",
      "store_name": "string or null",
      "priority": integer 0-10 or null
    }}
  ],
  "calendar": [
    {{
      "title": "string (required)",
      "description": "string or null",
      "location": "string or null",
      "start_time": "ISO 8601 datetime string (required)",
      "end_time": "ISO 8601 datetime string or null",
      "all_day": boolean,
      "reminder_minutes": integer or null,
      "url": "string or null",
      "attendees": "string or null"
    }}
  ]
}}

CRITICAL RULES:
- Output ONLY valid JSON, nothing else
- NO markdown formatting, NO code blocks, NO ```json``` tags
- Use null for missing optional fields (not "null" string)
- Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SS)
- Infer reasonable values when possible"""

        try:
            message = self.client.messages.create(
                model=settings.llm_model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text.strip()

            # Clean up potential markdown formatting
            response_text = (
                response_text.replace("```json\n", "")
                .replace("```\n", "")
                .replace("```", "")
                .strip()
            )

            # Parse JSON response
            data = json.loads(response_text)

            # Convert to Pydantic models
            todos = [ParsedTodo(**item) for item in data.get("todos", [])]
            shopping = [ParsedShopping(**item) for item in data.get("shopping", [])]
            calendar = [ParsedCalendar(**item) for item in data.get("calendar", [])]

            return ParsedResult(todos=todos, shopping=shopping, calendar=calendar)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ParsingException(f"Failed to parse JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"Parsing failed: {str(e)}")
            raise ParsingException(f"Failed to parse user input: {str(e)}")
