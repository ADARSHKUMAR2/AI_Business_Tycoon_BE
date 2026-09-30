from fastapi import APIRouter, HTTPException, Query

from services.game.controllers.leaderboard_controller import LeaderboardController
from services.game.models.leaderboard import LeaderboardResponse


router = APIRouter(prefix="/leaderboards", tags=["Leaderboards"])


@router.get("/{metric}", response_model=LeaderboardResponse)
async def get_leaderboard(
    metric: str,
    limit: int = Query(20, ge=1, le=100),
):
    """Get the persisted competitive ranking for one supported metric."""
    try:
        return await LeaderboardController.get_leaderboard(metric, limit)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error