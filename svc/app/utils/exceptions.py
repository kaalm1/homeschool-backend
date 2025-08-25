from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


class HomeschoolException(Exception):
    """Base exception for homeschool application."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(HomeschoolException):
    """Validation error exception."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class AuthenticationError(HomeschoolException):
    """Authentication error exception."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(HomeschoolException):
    """Authorization error exception."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(HomeschoolException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ConflictError(HomeschoolException):
    """Resource conflict exception."""

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


async def homeschool_exception_handler(request: Request, exc: HomeschoolException):
    """Handle custom homeschool exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation exceptions."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error",
            "details": exc.errors(),
            "type": "ValidationError",
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Internal server error",
            "type": "InternalServerError",
        },
    )


def add_exception_handlers(app: FastAPI):
    """Add exception handlers to FastAPI app."""
    app.add_exception_handler(HomeschoolException, homeschool_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
