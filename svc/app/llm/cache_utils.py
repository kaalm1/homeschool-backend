# svc/app/llm/cache_utils.py
"""Utilities for managing the enum cache."""

from sqlalchemy.orm import Session

from svc.app.database import get_db_session
from svc.app.llm.enum_loader import enum_cache


def refresh_enum_cache():
    """Refresh the enum cache from database. Call this after adding themes/activity types."""
    db_session = next(get_db_session())
    try:
        enum_cache.refresh_themes(db_session)
        enum_cache.refresh_activity_types(db_session)
    finally:
        db_session.close()


def refresh_themes_cache():
    """Refresh only themes cache."""
    db_session = next(get_db_session())
    try:
        enum_cache.refresh_themes(db_session)
    finally:
        db_session.close()


def refresh_activity_types_cache():
    """Refresh only activity types cache."""
    db_session = next(get_db_session())
    try:
        enum_cache.refresh_activity_types(db_session)
    finally:
        db_session.close()
