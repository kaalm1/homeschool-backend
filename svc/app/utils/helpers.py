import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


def snake_case_to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase."""
    components = snake_str.split("_")
    return components[0] + "".join(word.capitalize() for word in components[1:])


def camel_case_to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def filter_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None values from dictionary."""
    return {k: v for k, v in data.items() if v is not None}


def calculate_pagination_info(total: int, page: int, size: int) -> Dict[str, int]:
    """Calculate pagination information."""
    pages = (total + size - 1) // size  # Ceiling division
    return {
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }


def model_to_dict(model: BaseModel, exclude_none: bool = True) -> Dict[str, Any]:
    """Convert Pydantic model to dictionary."""
    return model.model_dump(exclude_none=exclude_none)


def format_validation_error(error: Exception) -> str:
    """Format validation error for user-friendly message."""
    if hasattr(error, "errors"):
        messages = []
        for err in error.errors():
            field = " -> ".join(str(x) for x in err["loc"])
            message = err["msg"]
            messages.append(f"{field}: {message}")
        return "; ".join(messages)
    return str(error)
