"""World state routes for Phase 4 weather and day/night simulation."""

from fastapi import APIRouter

from services.game.controllers.world_state_controller import WorldStateController
from services.game.models.world_state import WorldStateResponse

router = APIRouter(prefix="/world", tags=["World"])


@router.get("/state", response_model=WorldStateResponse, summary="Get shared world time and weather")
async def get_world_state() -> WorldStateResponse:
    return WorldStateController.get_world_state()