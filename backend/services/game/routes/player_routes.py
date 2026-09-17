from fastapi import APIRouter, HTTPException, Path
from typing import List

from services.game.models.player import PlayerState, PlayerCreate, PlayerUpdate
from services.game.controllers.player_controller import PlayerController

router = APIRouter(prefix="/player", tags=["Player"])

@router.post("/new", response_model=PlayerState)
async def create_player(player_data: PlayerCreate):
    """Create a new player."""
    return PlayerController.create_player(player_data)

@router.get("/list", response_model=List[str])
async def get_all_players():
    """List all player IDs."""
    return PlayerController.get_all_players()

@router.get("/{player_id}", response_model=PlayerState)
async def get_player(player_id: str = Path(..., description="Player ID")):
    """Get player state by ID."""
    return PlayerController.get_player(player_id)

@router.put("/{player_id}", response_model=PlayerState)
async def update_player(
    update_data: PlayerUpdate,
    player_id: str = Path(..., description="Player ID")
):
    """Update player details."""
    return PlayerController.update_player(player_id, update_data)

@router.delete("/{player_id}")
async def delete_player(player_id: str = Path(..., description="Player ID")):
    """Delete player data."""
    return PlayerController.delete_player(player_id)
