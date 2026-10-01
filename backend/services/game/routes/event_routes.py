from fastapi import APIRouter, Path
from typing import Optional
from services.game.models.events import FranchiseEvent, EventCreate, EventResponse
from services.game.models.business import Business
from services.game.controllers.event_controller import EventController

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/create", response_model=FranchiseEvent)
async def create_event(data: EventCreate):
    """ADMIN ONLY: Create a new franchise tournament."""
    return await EventController.create_event(data)

@router.get("/active", response_model=Optional[EventResponse])
async def get_active_event(player_id: str = None):
    """Get the current active or upcoming event. Pass player_id to check registration status."""
    return await EventController.get_active_event(player_id)

@router.post("/{event_id}/register/{player_id}", response_model=EventResponse)
async def register_for_event(
    event_id: str = Path(...),
    player_id: str = Path(...)
):
    """Register a player for an event and deduct the entry fee."""
    return await EventController.register_player(event_id, player_id)

@router.post("/{event_id}/create-business/{player_id}", response_model=Business)
async def create_event_business(
    event_id: str = Path(...),
    player_id: str = Path(...)
):
    """Create a temporary franchise business for the player to participate in the event."""
    return await EventController.create_event_business(event_id, player_id)
