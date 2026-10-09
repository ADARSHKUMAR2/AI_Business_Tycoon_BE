"""
Custom exceptions for AI Business Tycoon Backend.

This module also contains the shared request-error logging helpers used by
FastAPI services. Exceptions remain data-only; logging happens in handlers
where the request context is available.
"""
import json
import logging
from typing import Any, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError


MAX_LOG_BODY_LENGTH = 10_000


def _request_body_for_log(body: bytes) -> str:
    """Return a bounded, useful representation of a request body."""
    if not body:
        return "<empty>"

    try:
        value = json.loads(body)
        body_text = json.dumps(value, ensure_ascii=False, default=str)
    except (UnicodeDecodeError, json.JSONDecodeError):
        body_text = body.decode("utf-8", errors="replace")

    if len(body_text) > MAX_LOG_BODY_LENGTH:
        return f"{body_text[:MAX_LOG_BODY_LENGTH]}... [truncated]"
    return body_text


def log_business_exception(logger: logging.Logger, request: Request, exc: "BusinessTycoonException") -> None:
    """Log a handled business exception with enough request context to debug it."""
    logger.warning(
        "API request failed | method=%s path=%s query=%s status=%s exception=%s "
        "message=%s details=%s",
        request.method,
        request.url.path,
        request.url.query or "<none>",
        exc.status_code,
        type(exc).__name__,
        exc.message,
        exc.details,
    )


async def log_request_validation_error(
    logger: logging.Logger,
    request: Request,
    exc: RequestValidationError,
) -> None:
    """Log FastAPI/Pydantic validation failures, including the submitted body."""
    body = await request.body()
    logger.warning(
        "API request validation failed | method=%s path=%s query=%s status=422 "
        "errors=%s body=%s",
        request.method,
        request.url.path,
        request.url.query or "<none>",
        exc.errors(),
        _request_body_for_log(body),
    )


class BusinessTycoonException(Exception):
    """Base exception for all custom exceptions."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Any] = None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundError(BusinessTycoonException):
    """Resource not found exception."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, status_code=404)


class AlreadyExistsError(BusinessTycoonException):
    """Resource already exists exception."""
    
    def __init__(self, resource: str, identifier: str):
        message = f"{resource} with id '{identifier}' already exists"
        super().__init__(message, status_code=409)


class InsufficientFundsError(BusinessTycoonException):
    """Insufficient funds exception."""
    
    def __init__(self, required: float, available: float):
        message = f"Insufficient funds. Required: ₹{required:.2f}, Available: ₹{available:.2f}"
        super().__init__(message, status_code=400, details={"required": required, "available": available})


class InvalidOperationError(BusinessTycoonException):
    """Invalid operation exception."""
    
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class ValidationError(BusinessTycoonException):
    """Validation error exception."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else None
        super().__init__(message, status_code=422, details=details)


class StateManagerError(BusinessTycoonException):
    """State management error exception."""
    
    def __init__(self, message: str):
        super().__init__(f"State management error: {message}", status_code=500)