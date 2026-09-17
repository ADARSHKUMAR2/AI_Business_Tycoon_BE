from fastapi import APIRouter, Path
from typing import List, Dict, Any

from services.game.models.land import LandPurchaseRequest, LandTile
from services.game.controllers.land_controller import LandController

router = APIRouter(prefix="/land", tags=["Land"])

@router.get("/{player_id}/available", response_model=List[Dict[str, Any]])
async def get_available_land(player_id: str = Path(...)):
    """Get available adjacent tiles and their cost."""
    return await LandController.get_available_land(player_id)

@router.post("/purchase", response_model=LandTile)
async def purchase_land(request: LandPurchaseRequest):
    """Purchase a new land tile."""
    return await LandController.purchase_land(request)
