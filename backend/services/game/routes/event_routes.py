from fastapi import APIRouter, Path
from typing import Optional
from pydantic import BaseModel
from services.game.models.events import FranchiseEvent, EventCreate, EventResponse
from services.game.models.business import Business
from services.game.controllers.event_controller import EventController
from services.game.controllers.leaderboard_controller import LeaderboardController

router = APIRouter(prefix="/events", tags=["Events"])


class EventBusinessPlacementRequest(BaseModel):
    """Grid coordinates on the player's owned land where the event store should be placed."""
    position_x: int
    position_y: int


@router.post("/create", response_model=FranchiseEvent)
async def create_event(data: EventCreate):
    """ADMIN ONLY: Create a new franchise tournament."""
    return await EventController.create_event(data)


@router.get("/active", response_model=Optional[EventResponse])
async def get_active_event(player_id: str = None):
    """Get the current active or upcoming event."""
    return await EventController.get_active_event(player_id)


@router.post("/{event_id}/register/{player_id}", response_model=EventResponse)
async def register_for_event(
    event_id: str = Path(...),
    player_id: str = Path(...),
):
    """Register a player for an event and deduct the entry fee."""
    return await EventController.register_player(event_id, player_id)


@router.post("/{event_id}/create-business/{player_id}", response_model=Business)
async def create_event_business(
    placement: EventBusinessPlacementRequest,
    event_id: str = Path(...),
    player_id: str = Path(...),
):
    """
    Place the temporary franchise event store on a grid tile the player already owns.
    The tile must be owned and currently empty (no other business on it).
    If the player wins the event the store becomes permanent at that location.
    If they lose it is removed during event resolution.
    """
    return await EventController.create_event_business(
        event_id, player_id, placement.position_x, placement.position_y
    )


@router.get("/leaderboard")
async def get_event_leaderboard():
    """
    REST endpoint for the event leaderboard.
    Used by Unity when the event is COMPLETED (frozen results, no WebSocket needed).
    For ACTIVE events, Unity uses the WebSocket stream for live updates.
    """
    result = await LeaderboardController.get_event_leaderboard()
    if result is None:
        return {"event_id": None, "franchise_name": None, "time_remaining_seconds": 0, "entries": []}
    return result
