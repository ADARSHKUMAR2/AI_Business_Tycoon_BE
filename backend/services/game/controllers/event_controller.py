from datetime import datetime, timedelta
from typing import Optional, List
from services.game.models.events import FranchiseEvent, EventStatus, EventCreate, EventResponse
from services.game.models.business import Business, BusinessType
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
    
    @staticmethod
    async def create_event_business(event_id: str, player_id: str) -> Business:
        """Create a temporary franchise business for a player in an event."""
        event = await FranchiseEvent.find_one({"event_id": event_id})
        if not event:
            raise NotFoundError("Event", event_id)
        
        if event.status == EventStatus.COMPLETED:
            raise InvalidOperationError("Cannot create business for completed event.")
        
        if player_id not in event.participants:
            raise InvalidOperationError("Player must be registered for the event first.")
        
        player = await state_manager.load_player(player_id)
        
        # Check if player already has an event business for this event
        for biz in player.businesses:
            if biz.is_event_business and biz.event_id == event_id:
                return biz  # Already has event business
        
        # Determine business type based on franchise name
        business_type = BusinessType.CAFE  # Default for Starbucks
        if "pizza" in event.franchise_name.lower():
            business_type = BusinessType.PIZZA
        elif "restaurant" in event.franchise_name.lower():
            business_type = BusinessType.RESTAURANT
        elif "kirana" in event.franchise_name.lower():
            business_type = BusinessType.KIRANA
        
        # Create event business at designated event zone (position 100, 0)
        event_business = Business(
            player_id=player_id,
            business_type=business_type,
            name=f"{event.franchise_name} Event",
            position_x=100,  # Event zone
            position_y=0,
            is_event_business=True,
            event_id=event_id,
            inventory={},  # Will be stocked with default items
            employees=[],
            is_open=True
        )
        
        # Add default inventory based on business type
        if business_type == BusinessType.CAFE:
            event_business.inventory = {
                "coffee": {"name": "Coffee", "cost": 20.0, "price": 40.0, "stock": 50, "max_stock": 50, "total_sold": 0},
                "pastry": {"name": "Pastry", "cost": 30.0, "price": 60.0, "stock": 30, "max_stock": 30, "total_sold": 0}
            }
        
        player.businesses.append(event_business)
        player.stats.businesses_owned += 1
        
        await state_manager.save_player(player)
        
        return event_business
