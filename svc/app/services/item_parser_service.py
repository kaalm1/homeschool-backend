import json
from typing import Optional

from svc.app.datatypes.calendar import ParsedCalendar
from svc.app.datatypes.results import ParsedResult
from svc.app.datatypes.shopping import ParsedShopping
from svc.app.datatypes.todo import ParsedTodo
from svc.app.llm.client import llm_client


class ItemParserService:
    """Service for parsing user input using Claude AI"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the parser service with Anthropic API key"""
        self.client = llm_client

    def parse_user_input(self, user_input: str) -> ParsedResult:
        """
        Parse raw user input and categorize into todos, shopping, and calendar items.

        Args:
            user_input: Raw text from user containing mixed items

        Returns:
            ParsedResult containing categorized items
        """
        prompt = f"""You are a smart assistant that categorizes user input into three types:
1. TODO items - tasks, things to do, reminders
2. SHOPPING items - things to buy, groceries, items to purchase
3. CALENDAR events - appointments, meetings, scheduled events

Analyze the following user input and extract all items, categorizing each one appropriately.

User input: {user_input}

Respond ONLY with valid JSON in this EXACT format (no markdown, no extra text):
{{
  "todos": [
    {{
      "title": "string (required)",
      "description": "string or null",
      "priority": "high/medium/low or null",
      "due_date": "ISO 8601 datetime string or null"
    }}
  ],
  "shopping": [
    {{
      "item_name": "string (required)",
      "quantity": "string or null",
      "category": "string or null",
      "notes": "string or null",
      "estimated_price": "string or null"
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
      "reminder_minutes": integer or null
    }}
  ]
}}

IMPORTANT: 
- Output ONLY valid JSON, nothing else
- Use null for missing optional fields
- Use ISO 8601 format for dates (YYYY-MM-DDTHH:MM:SS)
- Infer reasonable values when possible (e.g., if user says "dentist appointment tomorrow at 2pm", calculate the actual datetime)
- Current datetime for reference: {datetime.now().isoformat()}"""

        message = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response
        data = json.loads(response_text)

        # Convert to dataclasses
        todos = [ParsedTodo(**item) for item in data.get("todos", [])]
        shopping = [ParsedShopping(**item) for item in data.get("shopping", [])]
        calendar = [ParsedCalendar(**item) for item in data.get("calendar", [])]

        return ParsedResult(todos=todos, shopping=shopping, calendar=calendar)
