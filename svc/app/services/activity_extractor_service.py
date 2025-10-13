import json
import os
from dataclasses import dataclass
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from svc.app.config import settings
from svc.app.llm.client import llm_client


@dataclass
class Activity:
    title: str
    description: Optional[str] = None
    website: Optional[str] = None
    price: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "website": self.website,
            "price": self.price,
            "location": self.location,
        }


class ActivityExtractor:
    def __init__(self):
        """
        Initialize the extractor with optional Anthropic API key for LLM extraction.
        If no API key provided, will only use basic scraping.
        """
        self.client = llm_client.client
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_retries = settings.llm_max_retries

    def fetch_webpage(self, url: str) -> str:
        """Fetch the HTML content of a webpage."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text

    def clean_text(self, html: str) -> str:
        """Extract and clean text from HTML."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text

    def extract_with_llm(self, text: str, url: str) -> List[Activity]:
        """Use Claude to extract structured activity data from text."""
        if not self.client:
            raise ValueError(
                "Anthropic API key not provided. Cannot use LLM extraction."
            )

        # Define JSON schema for structured output
        json_schema = {
            "name": "activity_extraction",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "activities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The name/title of the activity",
                                },
                                "description": {
                                    "type": ["string", "null"],
                                    "description": "A brief description of what the activity is",
                                },
                                "website": {
                                    "type": ["string", "null"],
                                    "description": "Any URL mentioned for the activity",
                                },
                                "price": {
                                    "type": ["string", "null"],
                                    "description": "Cost information (e.g., 'Free', '$10', '$5-$15')",
                                },
                                "location": {
                                    "type": ["string", "null"],
                                    "description": "Where the activity takes place (address, venue name, or area)",
                                },
                            },
                            "required": [
                                "title",
                                "description",
                                "website",
                                "price",
                                "location",
                            ],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["activities"],
                "additionalProperties": False,
            },
        }

        prompt = f"""Analyze the following webpage content and extract ALL activities, events, or things to do mentioned.

For each activity, extract:
- title: The name/title of the activity (required, must not be empty)
- description: A brief description of what the activity is (null if not available)
- website: Any URL mentioned for the activity (null if not available)
- price: Cost information like "Free", "$10", "$5-$15" (null if not available)
- location: Where the activity takes place - address, venue name, or area (null if not available)

Webpage URL: {url}

Content:
{text[:15000]}"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_schema", "json_schema": json_schema},
        )

        response_text = message.content[0].text.strip()

        # Parse JSON response (guaranteed valid with structured output)
        response_data = json.loads(response_text)
        activities_data = response_data.get("activities", [])

        # Convert to Activity objects
        activities = []
        for data in activities_data:
            activities.append(
                Activity(
                    title=data.get("title", ""),
                    description=data.get("description"),
                    website=data.get("website"),
                    price=data.get("price"),
                    location=data.get("location"),
                )
            )

        return activities

    def basic_scrape(self, html: str, url: str) -> List[Activity]:
        """Basic scraping fallback - tries to find structured activity data."""
        soup = BeautifulSoup(html, "html.parser")
        activities = []

        # Look for common patterns (articles, event listings, etc.)
        # This is a simple example - you'd expand this based on common patterns

        articles = soup.find_all(
            ["article", "div"],
            class_=lambda x: x
            and any(
                term in str(x).lower()
                for term in ["event", "activity", "listing", "item"]
            ),
        )

        for article in articles[:20]:  # Limit to 20 items
            title_elem = article.find(["h1", "h2", "h3", "h4", "a"])
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            description = None

            # Try to find description
            desc_elem = article.find(
                ["p", "div"], class_=lambda x: x and "desc" in str(x).lower()
            )
            if desc_elem:
                description = desc_elem.get_text(strip=True)[:500]

            if title and len(title) > 5:
                activities.append(Activity(title=title, description=description))

        return activities if activities else None

    def extract_activities(self, url: str, use_llm: bool = True) -> List[Activity]:
        """
        Main method to extract activities from a URL.

        Args:
            url: The webpage URL to scrape
            use_llm: Whether to use LLM extraction (default: True)

        Returns:
            List of Activity objects
        """
        print(f"Fetching content from: {url}")
        html = self.fetch_webpage(url)

        if use_llm and self.client:
            print("Extracting activities using LLM...")
            text = self.clean_text(html)
            activities = self.extract_with_llm(text, url)
        else:
            print("Using basic scraping (no LLM)...")
            activities = self.basic_scrape(html, url)
            if not activities:
                print(
                    "Basic scraping found no activities. Consider using LLM extraction."
                )
                activities = []

        print(f"Found {len(activities)} activities")
        return activities
