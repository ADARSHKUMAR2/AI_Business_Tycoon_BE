from fastapi import APIRouter, Path, Query
from typing import List

from services.game.models.business import Business, BusinessCreate
from services.game.models.inventory import InventoryUpdate, PriceUpdate
from services.game.controllers.business_controller import BusinessController

router = APIRouter(prefix="/business", tags=["Business"])

@router.post("/create", response_model=Business)
async def create_business(data: BusinessCreate):
    """Create a new business."""
    return await BusinessController.create_business(data)

@router.get("/{player_id}/{business_id}", response_model=Business)
async def get_business(
    player_id: str = Path(..., description="Player ID"),
    business_id: str = Path(..., description="Business ID")
):
    """Get business details."""
    return await BusinessController.get_business(player_id, business_id)

@router.put("/{player_id}/{business_id}/inventory", response_model=Business)
async def update_inventory(
    update_data: InventoryUpdate,
    player_id: str = Path(...),
    business_id: str = Path(...)
):
    """Update business inventory (restock or change price)."""
    return await BusinessController.update_inventory(player_id, business_id, update_data)

@router.put("/{player_id}/{business_id}/price", response_model=Business)
async def update_price_multiplier(
    update_data: PriceUpdate,
    player_id: str = Path(...),
    business_id: str = Path(...)
):
    """Update business global price multiplier."""
    return await BusinessController.set_price_multiplier(player_id, business_id, update_data)

@router.post("/{player_id}/{business_id}/toggle", response_model=Business)
async def toggle_business_status(
    is_open: bool = Query(..., description="True to open, False to close"),
    player_id: str = Path(...),
    business_id: str = Path(...)
):
    """Open or close the business."""
    return await BusinessController.toggle_business_status(player_id, business_id, is_open)
