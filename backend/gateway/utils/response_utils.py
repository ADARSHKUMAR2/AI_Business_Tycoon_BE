"""Response utility formatters."""
from typing import Any, Dict, Optional
from fastapi.responses import JSONResponse

def success_response(data: Any, message: str = "Success") -> Dict[str, Any]:
    """Format a successful response."""
    return {
        "success": True,
        "message": message,
        "data": data
    }

def error_response(message: str, status_code: int = 400, details: Optional[Any] = None) -> JSONResponse:
    """Format an error response."""
    content = {
        "success": False,
        "error": {
            "message": message,
            "details": details
        }
    }
    return JSONResponse(status_code=status_code, content=content)
