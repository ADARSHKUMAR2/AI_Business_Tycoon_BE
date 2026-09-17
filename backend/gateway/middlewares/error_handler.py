"""Global error handler middleware."""
from fastapi import Request
from fastapi.responses import JSONResponse
from shared.exceptions import BusinessTycoonException
from gateway.utils.response_utils import error_response
import logging

logger = logging.getLogger("gateway")

async def custom_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle custom business logic exceptions."""
    
    if isinstance(exc, BusinessTycoonException):
        # Known custom exception
        return error_response(
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details
        )
        
    # Unhandled exception (500)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return error_response(
        message="Internal server error",
        status_code=500,
        details=str(exc) if "development" in str(request.app.title).lower() else None
    )
