from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scripts.seed_data import seed_demo_data
from svc.app.database import get_raw_db_session

from .config import get_settings
from .controllers import (
    activity_controller,
    auth_controller,
    kid_controller,
    reward_controller,
)
from .database import create_tables
from .utils.exceptions import add_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    create_tables()
    await seed_demo_data()
    yield
    # Shutdown
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Homeschool Helper API",
        description="A comprehensive homeschool management API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    origins = [origin.strip() for origin in settings.cors_origins.split(",")]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add exception handlers
    add_exception_handlers(app)

    # Include routers
    app.include_router(
        auth_controller.router, prefix="/api/v1/auth", tags=["Authentication"]
    )
    app.include_router(kid_controller.router, prefix="/api/v1/kids", tags=["Kids"])
    app.include_router(
        activity_controller.router, prefix="/api/v1/activities", tags=["Activities"]
    )
    app.include_router(
        reward_controller.router, prefix="/api/v1/rewards", tags=["Rewards"]
    )

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "homeschool-api"}

    return app


app = create_app()
