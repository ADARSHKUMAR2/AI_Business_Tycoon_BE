"""
Custom exceptions for AI Business Tycoon Backend
"""
from typing import Any, Optional


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