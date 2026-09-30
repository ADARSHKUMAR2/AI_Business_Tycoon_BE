from datetime import datetime, timedelta
from typing import Optional, List
from services.game.models.events import FranchiseEvent, EventStatus, EventCreate, EventResponse
from services.game.utils.state_manager import state_manager
from shared.exceptions import BusinessTycoonException, NotFoundError, InvalidOperationError

class EventController:
    @staticmethod
    async def create_event(data: EventCreate) -> FranchiseEvent:
        """Admin: Create a new franchise tournament event."""
        # Check if there is already an active or upcoming event
        existing = await FranchiseEvent.find_one({"status": {"$in": [EventStatus.UPCOMING, EventStatus.ACTIVE]}})
        if existing:
            raise InvalidOperationError(f"An event is already {existing.status.value}: {existing.franchise_name}")

        now = datetime.utcnow()
        event = FranchiseEvent(
            franchise_name=data.franchise_name,
            status=EventStatus.UPCOMING,
            start_time=now, # In a real system, you might schedule this for the future
            end_time=now + timedelta(minutes=data.duration_minutes),
            entry_fee=data.entry_fee,
            max_winners=data.max_winners,
            participants={}
        )
        await event.save()
        return event

    @staticmethod
    async def get_active_event(player_id: str = None) -> Optional[EventResponse]:
        """Get the currently active or upcoming event."""
        event = await FranchiseEvent.find_one({"status": {"$in": [EventStatus.UPCOMING, EventStatus.ACTIVE]}})
        if not event:
            return None
            
        # Auto-update status if time has passed
        now = datetime.utcnow()
        if event.status == EventStatus.UPCOMING and now >= event.start_time:
            if now >= event.end_time:
                event.status = EventStatus.COMPLETED
            else:
                event.status = EventStatus.ACTIVE
            await event.save()
        elif event.status == EventStatus.ACTIVE and now >= event.end_time:
            event.status = EventStatus.COMPLETED
            await event.save()
            return None # Don't return completed events here
            
        is_reg = False
        if player_id and player_id in event.participants:
            is_reg = True
            
        return EventResponse(
            event_id=event.event_id,
            franchise_name=event.franchise_name,
            status=event.status.value,
            start_time=event.start_time,
            end_time=event.end_time,
            entry_fee=event.entry_fee,
            max_winners=event.max_winners,
            is_registered=is_reg,
            participant_count=len(event.participants)
        )

    @staticmethod
    async def register_player(event_id: str, player_id: str) -> EventResponse:
        """Register a player for an event, deducting the entry fee."""
        event = await FranchiseEvent.find_one({"event_id": event_id})
        if not event:
            raise NotFoundError("Event", event_id)
            
        if event.status == EventStatus.COMPLETED:
            raise InvalidOperationError("This event has already ended.")
            
        if player_id in event.participants:
            raise InvalidOperationError("Player is already registered for this event.")
            
        player = await state_manager.load_player(player_id)
        
        if not player.deduct_money(event.entry_fee):
            raise InvalidOperationError(f"Insufficient funds. Entry fee is ₹{event.entry_fee}")
            
        # Add to participants with 0 starting revenue
        event.participants[player_id] = 0.0
        
        await state_manager.save_player(player)
        await event.save()
        
        return await EventController.get_active_event(player_id)
