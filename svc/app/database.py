from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

from .config import get_settings


settings = get_settings()

# Configure engine based on database type
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db_session():
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
