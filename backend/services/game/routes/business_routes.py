from fastapi import APIRouter, Path, Query
from typing import List

from services.game.models.business import Business, BusinessCreate
from services.game.models.inventory import InventoryUpdate, PriceUpdate, ShelfUpgradeRequest
from services.game.models.trash import TrashItem, SpawnTrashRequest
from services.game.controllers.business_controller import BusinessController

router = APIRouter(prefix="/business", tags=["Business"])

# ── Business CRUD ──────────────────────────────────────────────────────

@router.post("/create", response_model=Business)
async def create_business(data: BusinessCreate):
    """Create a new business on an owned land tile."""
    return await BusinessController.create_business(data)


@router.get("/{player_id}/{business_id}", response_model=Business)
async def get_business(
    player_id:   str = Path(..., description="Player ID"),
    business_id: str = Path(..., description="Business ID"),
):
    """Get full business state (inventory, employees, trash, rating)."""
    return await BusinessController.get_business(player_id, business_id)

# ── Inventory ──────────────────────────────────────────────────────────

@router.put("/{player_id}/{business_id}/inventory", response_model=Business)
async def update_inventory(
    update_data: InventoryUpdate,
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """Restock an item or change its selling price."""
    return await BusinessController.update_inventory(player_id, business_id, update_data)


@router.put("/{player_id}/{business_id}/price", response_model=Business)
async def update_price_multiplier(
    update_data: PriceUpdate,
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """Update the global price multiplier for all items in a business."""
    return await BusinessController.set_price_multiplier(player_id, business_id, update_data)

@router.post("/{player_id}/{business_id}/toggle", response_model=Business)
async def toggle_business_status(
    is_open:     bool = Query(..., description="True to open, False to close"),
    player_id:   str  = Path(...),
    business_id: str  = Path(...),
):
    """Open or close the business."""
    return await BusinessController.toggle_business_status(player_id, business_id, is_open)

# ── Phase 3: Shelf Upgrades ────────────────────────────────────────────

@router.post("/{player_id}/{business_id}/shelf/upgrade", response_model=Business)
async def upgrade_shelf(
    request:     ShelfUpgradeRequest,
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """
    Upgrade the max capacity of a shelf.
    Body: { "item_key": "rice", "target_capacity": 20 }
    Valid target capacities: 20 (₹2,000) or 30 (₹5,000).
    """
    return await BusinessController.upgrade_shelf(player_id, business_id, request)


# ── Phase 3: Trash / Cleanliness ──────────────────────────────────────

@router.get("/{player_id}/{business_id}/trash", response_model=List[TrashItem])
async def get_trash(
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """
    Get all active trash items on the store floor.
    Call this on game load so the Cleaner AI knows what to clean.
    """
    return await BusinessController.get_trash(player_id, business_id)


@router.post("/{player_id}/{business_id}/trash", response_model=Business)
async def spawn_trash(
    request:     SpawnTrashRequest,
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """
    Spawn a trash item at the given world position.
    Called by Godot when a customer drops trash.
    Body: { "position_x": 145.5, "position_y": 230.0 }
    """
    return await BusinessController.spawn_trash(player_id, business_id, request)


@router.delete("/{player_id}/{business_id}/trash/{trash_id}", response_model=Business)
async def remove_trash(
    player_id:   str = Path(...),
    business_id: str = Path(...),
    trash_id:    str = Path(...),
):
    """
    Remove a trash item by ID (Cleaner AI has cleaned it).
    Returns the updated Business with the new store_rating.
    """
    return await BusinessController.remove_trash(player_id, business_id, trash_id)
