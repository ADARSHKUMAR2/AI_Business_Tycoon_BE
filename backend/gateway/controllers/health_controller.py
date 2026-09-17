from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ai-business-tycoon-backend",
        "timestamp": datetime.utcnow().isoformat()
    }
