from datetime import datetime, timedelta
from typing import Optional

from services.game.models.events import (
    FranchiseEvent,
    EventStatus,
    EventCreate,
    EventResponse,
)
from services.game.models.business import Business, BusinessType
from services.game.models.land import LandType
from services.game.utils.state_manager import state_manager
from shared.exceptions import NotFoundError, InvalidOperationError


class EventController:
    @staticmethod
    async def create_event(data: EventCreate) -> FranchiseEvent:
        """Admin: Create a new franchise tournament event."""
        existing = await FranchiseEvent.find_one(
            {"status": {"$in": [EventStatus.UPCOMING, EventStatus.ACTIVE]}}
        )
        if existing:
            raise InvalidOperationError(
                f"An event is already {existing.status.value}: "
                f"{existing.franchise_name}"
            )

        now = datetime.utcnow()
        event = FranchiseEvent(
            franchise_name=data.franchise_name,
            status=EventStatus.UPCOMING,
            start_time=now,
            end_time=now + timedelta(minutes=data.duration_minutes),
            entry_fee=data.entry_fee,
            max_winners=data.max_winners,
            participants={},
        )
        await event.save()
        return event

    @staticmethod
    async def get_active_event(
        player_id: str = None,
    ) -> Optional[EventResponse]:
        """Get the current or recently completed franchise event."""
        now = datetime.utcnow()
        grace_period_cutoff = now - timedelta(hours=24)

        event = await FranchiseEvent.find_one(
            {
                "status": {
                    "$in": [
                        EventStatus.UPCOMING,
                        EventStatus.ACTIVE,
                    ]
                }
            }
        )

        if not event:
            event = await FranchiseEvent.find_one(
                {
                    "status": EventStatus.COMPLETED,
                    "end_time": {"$gte": grace_period_cutoff},
                },
                sort=[("end_time", -1)],
            )

        if not event:
            return None

        if event.status == EventStatus.UPCOMING and now >= event.start_time:
            event.status = (
                EventStatus.COMPLETED
                if now >= event.end_time
                else EventStatus.ACTIVE
            )
            await event.save()
        elif event.status == EventStatus.ACTIVE and now >= event.end_time:
            event.status = EventStatus.COMPLETED
            await event.save()

        if event.status == EventStatus.COMPLETED and not event.resolved:
            await EventController.resolve_event(event)

        is_registered = bool(
            player_id and player_id in event.participants
        )

        return EventResponse(
            event_id=event.event_id,
            franchise_name=event.franchise_name,
            status=event.status.value,
            start_time=event.start_time,
            end_time=event.end_time,
            entry_fee=event.entry_fee,
            max_winners=event.max_winners,
            is_registered=is_registered,
            participant_count=len(event.participants),
            winners=event.winners,
        )

    @staticmethod
    async def register_player(
        event_id: str,
        player_id: str,
    ) -> EventResponse:
        """Register a player for an event and deduct the entry fee."""
        event = await FranchiseEvent.find_one({"event_id": event_id})
        if not event:
            raise NotFoundError("Event", event_id)

        if event.status == EventStatus.COMPLETED:
            raise InvalidOperationError("This event has already ended.")

        if player_id in event.participants:
            raise InvalidOperationError(
                "Player is already registered for this event."
            )

        player = await state_manager.load_player(player_id)

        if not player.deduct_money(event.entry_fee):
            raise InvalidOperationError(
                f"Insufficient funds. Entry fee is ₹{event.entry_fee}"
            )

        event.participants[player_id] = 0.0

        await state_manager.save_player(player)
        await event.save()

        return await EventController.get_active_event(player_id)

    @staticmethod
    async def resolve_event(event: FranchiseEvent) -> None:
        """
        Turn winners' temporary stores into permanent businesses and remove
        losing event businesses.
        """
        if event.resolved:
            return

        sorted_participants = sorted(
            event.participants.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        eligible_participants = [
            participant
            for participant in sorted_participants
            if participant[1] > 0
        ]

        winners = [
            player_id
            for player_id, _ in eligible_participants[: event.max_winners]
        ]
        event.winners = winners

        for player_id in event.participants.keys():
            try:
                player = await state_manager.load_player(player_id)
                businesses_to_keep = []
                player_updated = False

                for business in player.businesses:
                    is_this_event_business = (
                        business.is_event_business
                        and business.event_id == event.event_id
                    )

                    if not is_this_event_business:
                        businesses_to_keep.append(business)
                        continue

                    player_updated = True

                    for tile in player.land_tiles:
                        same_position = (
                            tile.position.x == business.position_x
                            and tile.position.y == business.position_y
                        )

                        if not same_position:
                            continue

                        if player_id in winners:
                            tile.tile_type = LandType.SHOP
                            tile.business_id = business.business_id
                        else:
                            tile.tile_type = LandType.EMPTY
                            tile.business_id = None

                        break

                    if player_id in winners:
                        business.is_event_business = False
                        business.event_id = None
                        business.name = f"{event.franchise_name} (Won!)"
                        businesses_to_keep.append(business)

                if player_updated:
                    player.businesses = businesses_to_keep
                    await state_manager.save_player(player)

            except Exception as error:
                print(
                    f"Error resolving event {event.event_id} "
                    f"for player {player_id}: {error}"
                )

        event.resolved = True
        await event.save()

    @staticmethod
    async def create_event_business(
        event_id: str,
        player_id: str,
        position_x: int,
        position_y: int,
    ) -> Business:
        """Create a temporary franchise business on an owned land tile."""
        event = await FranchiseEvent.find_one({"event_id": event_id})
        if not event:
            raise NotFoundError("Event", event_id)

        if event.status == EventStatus.COMPLETED:
            raise InvalidOperationError(
                "Cannot create business for completed event."
            )

        if player_id not in event.participants:
            raise InvalidOperationError(
                "Player must be registered for the event first."
            )

        player = await state_manager.load_player(player_id)

        existing_business = next(
            (
                business
                for business in player.businesses
                if business.position_x == position_x
                and business.position_y == position_y
            ),
            None,
        )

        if existing_business is not None:
            raise InvalidOperationError(
                f"Tile ({position_x}, {position_y}) is already occupied by "
                f"'{existing_business.name}'. Choose an empty tile for your "
                "event store."
            )

        selected_tile = next(
            (
                tile
                for tile in player.land_tiles
                if tile.position.x == position_x
                and tile.position.y == position_y
            ),
            None,
        )

        if selected_tile is None:
            raise InvalidOperationError(
                f"Tile ({position_x}, {position_y}) is not owned by this player."
            )

        if (
            selected_tile.tile_type == LandType.SHOP
            or selected_tile.business_id
        ):
            raise InvalidOperationError(
                f"Tile ({position_x}, {position_y}) is already occupied."
            )

        # Remove stale event businesses from older events. Preserve normal
        # businesses and the current event business if it already exists.
        cleaned_businesses = []

        for business in player.businesses:
            if business.is_event_business:
                if business.event_id == event_id:
                    return business

                continue

            cleaned_businesses.append(business)

        player.businesses = cleaned_businesses

        franchise_name = event.franchise_name.lower()
        business_type = BusinessType.CAFE

        if "pizza" in franchise_name:
            business_type = BusinessType.PIZZA
        elif "restaurant" in franchise_name:
            business_type = BusinessType.RESTAURANT
        elif "kirana" in franchise_name:
            business_type = BusinessType.KIRANA

        event_business = Business(
            player_id=player_id,
            business_type=business_type,
            name=f"{event.franchise_name} Event",
            position_x=position_x,
            position_y=position_y,
            is_event_business=True,
            event_id=event_id,
            inventory={},
            employees=[],
            is_open=True,
        )

        event_inventory_by_type = {
            BusinessType.KIRANA: {
                "rice": {
                    "name": "Rice (1kg)",
                    "cost": 40.0,
                    "price": 50.0,
                },
                "dal": {
                    "name": "Dal (1kg)",
                    "cost": 80.0,
                    "price": 100.0,
                },
                "milk": {
                    "name": "Milk (1L)",
                    "cost": 50.0,
                    "price": 60.0,
                },
                "bread": {
                    "name": "Bread",
                    "cost": 25.0,
                    "price": 35.0,
                },
            },
            BusinessType.PIZZA: {
                "margherita": {
                    "name": "Margherita Pizza",
                    "cost": 120.0,
                    "price": 250.0,
                },
                "pepperoni": {
                    "name": "Pepperoni Pizza",
                    "cost": 180.0,
                    "price": 350.0,
                },
                "garlic_bread": {
                    "name": "Garlic Bread",
                    "cost": 50.0,
                    "price": 120.0,
                },
                "cola": {
                    "name": "Cola (500ml)",
                    "cost": 30.0,
                    "price": 60.0,
                },
            },
            BusinessType.CAFE: {
                "espresso": {
                    "name": "Espresso",
                    "cost": 40.0,
                    "price": 120.0,
                },
                "cappuccino": {
                    "name": "Cappuccino",
                    "cost": 60.0,
                    "price": 180.0,
                },
                "croissant": {
                    "name": "Butter Croissant",
                    "cost": 45.0,
                    "price": 110.0,
                },
                "muffin": {
                    "name": "Blueberry Muffin",
                    "cost": 50.0,
                    "price": 130.0,
                },
            },
            BusinessType.RESTAURANT: {
                "tomato": {
                    "name": "Tomato",
                    "cost": 20.0,
                    "price": 40.0,
                },
                "onion": {
                    "name": "Onion",
                    "cost": 18.0,
                    "price": 35.0,
                },
                "lettuce": {
                    "name": "Lettuce",
                    "cost": 22.0,
                    "price": 45.0,
                },
                "flour": {
                    "name": "Flour",
                    "cost": 25.0,
                    "price": 50.0,
                },
            },
        }

        event_inventory = event_inventory_by_type[business_type]
        event_business.inventory = {
            item_key: {
                **item,
                "stock": 10,
                "max_stock": 10,
                "total_sold": 0,
            }
            for item_key, item in event_inventory.items()
        }

        selected_tile.tile_type = LandType.SHOP
        selected_tile.business_id = event_business.business_id

        player.businesses.append(event_business)
        player.stats.businesses_owned += 1

        await state_manager.save_player(player)

        return event_business
