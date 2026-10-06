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
        """Get the currently active, upcoming, or recently completed event (grace period)."""
        now = datetime.utcnow()
        # Find active/upcoming OR recently completed events (within last 24 hours)
        grace_period_cutoff = now - timedelta(hours=24)
        
        # Priority 1: Active or Upcoming
        event = await FranchiseEvent.find_one({"status": {"$in": [EventStatus.UPCOMING, EventStatus.ACTIVE]}})
        
        # Priority 2: Recently Completed (if no active/upcoming)
        if not event:
            event = await FranchiseEvent.find_one(
                {"status": EventStatus.COMPLETED, "end_time": {"$gte": grace_period_cutoff}},
                sort=[("end_time", -1)] # Get the most recent one
            )
            
        if not event:
            return None
            
        # Auto-update status if time has passed
        if event.status == EventStatus.UPCOMING and now >= event.start_time:
            if now >= event.end_time:
                event.status = EventStatus.COMPLETED
            else:
                event.status = EventStatus.ACTIVE
            await event.save()
        elif event.status == EventStatus.ACTIVE and now >= event.end_time:
            event.status = EventStatus.COMPLETED
            await event.save()
            
        # If it just completed (or was already completed), ensure it's resolved
        if event.status == EventStatus.COMPLETED and not event.resolved:
            await EventController.resolve_event(event)
            
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
            participant_count=len(event.participants),
            winners=event.winners
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
    async def resolve_event(event: FranchiseEvent) -> None:
        """Process an ended event: turn winners' temporary stores into permanent ones, delete losers' temporary stores."""
        if event.resolved:
            return
            
        # 1. Sort participants by revenue descending
        sorted_participants = sorted(event.participants.items(), key=lambda item: item[1], reverse=True)
        
        # 2. Identify winners
        winners = [p[0] for p in sorted_participants[:event.max_winners]]
        
        # Save winners list to the event document
        event.winners = winners
        
        # 3. Process all participants
        for player_id in event.participants.keys():
            try:
                player = await state_manager.load_player(player_id)
                businesses_to_keep = []
                player_updated = False
                
                for biz in player.businesses:
                    if biz.is_event_business and biz.event_id == event.event_id:
                        player_updated = True
                        if player_id in winners:
                            # WINNER: Store becomes permanent
                            biz.is_event_business = False
                            biz.event_id = None
                            biz.name = f"{event.franchise_name} (Won!)"
                            # We leave it at position (100, 0) for now. The player keeps it!
                            businesses_to_keep.append(biz)
                        else:
                            # LOSER: Store is deleted
                            pass # We simply don't add it to businesses_to_keep
                    else:
                        # Keep all normal businesses and businesses from other events
                        businesses_to_keep.append(biz)
                
                if player_updated:
                    player.businesses = businesses_to_keep
                    await state_manager.save_player(player)
            except Exception as e:
                # Log error but continue processing other players
                print(f"Error resolving event {event.event_id} for player {player_id}: {e}")
                
        # 4. Mark as resolved
        event.resolved = True
        await event.save()

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
        
        # CLEANUP: Remove any OLD dead event businesses the player might have stuck in their DB
        # from events that failed to resolve properly or were deleted.
        cleaned_businesses = []
        for biz in player.businesses:
            if biz.is_event_business:
                if biz.event_id == event_id:
                    return biz  # Already has business for THIS event, return it
                else:
                    # This is an old dead event business. Skip it (delete it).
                    pass
            else:
                cleaned_businesses.append(biz)
        
        player.businesses = cleaned_businesses
        
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
