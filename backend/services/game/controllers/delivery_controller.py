"""
Delivery controller for Phase 4 Feature 3.
Handles timed supply events and express restock purchases.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import Optional

from pymongo import ReturnDocument

from services.game.models.business import Business
from services.game.models.delivery import DeliveryStatusResponse
from services.game.models.player import PlayerState
from services.game.utils.state_manager import state_manager
from services.game.validators.player_validator import PlayerValidator
from shared.exceptions import InvalidOperationError, NotFoundError


class DeliveryController:
    """Manage supply truck deliveries for businesses."""

    @staticmethod
    def _restock_deliverable_inventory(business: Business) -> None:
        """Restock delivered supplies, excluding crafted products."""
        for item in business.inventory.values():
            if item.has_supply_zone:
                item.stock = item.max_stock

    @staticmethod
    async def _find_business_in_player(player: PlayerState, business_id: str) -> tuple[int, Business]:
        for idx, biz in enumerate(player.businesses):
            if biz.business_id == business_id:
                return idx, biz
        raise NotFoundError("Business", business_id)

    @staticmethod
    def _refresh_delivery_state(business: Business, now: Optional[datetime] = None) -> None:
        """
        Server-authoritative update:
        - Restock delivered supplies when a truck is due
        - Preserve the scheduled interval if status polling happens late
        """
        schedule = business.delivery_schedule
        if not schedule.is_active:
            return

        current = now or datetime.utcnow()

        if schedule.next_delivery_at is None:
            if schedule.last_delivery_at is None:
                schedule.last_delivery_at = current
            schedule.next_delivery_at = (
                schedule.last_delivery_at + timedelta(minutes=schedule.delivery_interval_minutes)
            )

        if current >= schedule.next_delivery_at:
            interval = timedelta(minutes=schedule.delivery_interval_minutes)
            elapsed_intervals = (current - schedule.next_delivery_at) // interval
            latest_delivery_at = schedule.next_delivery_at + elapsed_intervals * interval

            DeliveryController._restock_deliverable_inventory(business)
            schedule.last_delivery_at = latest_delivery_at
            schedule.next_delivery_at = latest_delivery_at + interval

        business.last_updated = current

    @staticmethod
    async def get_delivery_status(player_id: str, business_id: str) -> DeliveryStatusResponse:
        """
        Return the business's current supply status.
        This is what the Unity client polls.

        The status refresh is also authoritative: it updates the stored delivery schedule so the
        countdown is not recreated from the default 90-second supply window on every poll.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await DeliveryController._find_business_in_player(player, business_id)

        now = datetime.utcnow()
        DeliveryController._refresh_delivery_state(business, now)

        # Persist the refreshed delivery timing so the next API call reads from the current
        # business state rather than recreating a fresh default window from stale values.
        player.businesses[idx] = business
        await state_manager.save_player(player)

        schedule = business.delivery_schedule
        supply_available = schedule.is_supply_available(now)
        seconds_until_next = schedule.seconds_until_next(now)
        supply_window_remaining = schedule.seconds_until_supply_window_end(now)

        return DeliveryStatusResponse(
            business_id=business.business_id,
            supply_available=supply_available,
            seconds_until_next=seconds_until_next,
            supply_window_remaining=supply_window_remaining,
            last_delivery_at=schedule.last_delivery_at,
            next_delivery_at=schedule.next_delivery_at,
            delivery_interval_minutes=schedule.delivery_interval_minutes,
            express_delivery_cost=schedule.express_delivery_cost,
        )

    @staticmethod
    async def trigger_manual_restock(player_id: str, business_id: str) -> Business:
        """
        Force a restock for testing or admin operations.
        This is useful when you want to manually trigger a truck.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await DeliveryController._find_business_in_player(player, business_id)

        schedule = business.delivery_schedule
        if not schedule.is_active:
            raise InvalidOperationError("Delivery system is disabled for this business")

        now = datetime.utcnow()
        DeliveryController._restock_deliverable_inventory(business)

        schedule.mark_delivered(now)
        business.last_updated = now
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    @staticmethod
    async def request_express_delivery(
        player_id: str, business_id: str, idempotency_key: str
    ) -> Business:
        """Charge and deliver exactly once for a client-generated retry key."""
        collection = PlayerState.get_motor_collection()
        player_document = await collection.find_one({"player_id": player_id})
        if player_document is None:
            raise NotFoundError("Player", player_id)

        player = SimpleNamespace(
            player_id=player_id,
            money=player_document["money"],
            businesses=[Business.model_validate(item) for item in player_document["businesses"]],
        )
        _, business = await DeliveryController._find_business_in_player(player, business_id)
        schedule = business.delivery_schedule
        if not schedule.is_active:
            raise InvalidOperationError("Delivery system is disabled for this business")

        if idempotency_key in schedule.processed_express_delivery_keys:
            return business

        cost = schedule.express_delivery_cost
        PlayerValidator.validate_can_purchase(player, cost)

        now = datetime.utcnow()
        next_delivery_at = now + timedelta(minutes=schedule.delivery_interval_minutes)
        set_fields = {
            "businesses.$[biz].delivery_schedule.last_delivery_at": now,
            "businesses.$[biz].delivery_schedule.next_delivery_at": next_delivery_at,
            "businesses.$[biz].last_updated": now,
        }
        for item_key, item in business.inventory.items():
            if item.has_supply_zone:
                set_fields[f"businesses.$[biz].inventory.{item_key}.stock"] = item.max_stock

        collection = PlayerState.get_motor_collection()
        updated_player = await collection.find_one_and_update(
            {
                "player_id": player_id,
                "money": {"$gte": cost},
                "businesses": {
                    "$elemMatch": {
                        "business_id": business_id,
                        "delivery_schedule.is_active": True,
                        "delivery_schedule.processed_express_delivery_keys": {
                            "$ne": idempotency_key
                        },
                    }
                },
            },
            {
                "$inc": {
                    "money": -cost,
                    "stats.total_expenses": cost,
                },
                "$set": set_fields,
                "$push": {
                    "businesses.$[biz].delivery_schedule.processed_express_delivery_keys": (
                        idempotency_key
                    )
                },
            },
            array_filters=[{"biz.business_id": business_id}],
            return_document=ReturnDocument.AFTER,
        )

        if updated_player is not None:
            updated_business = next(
                biz for biz in updated_player["businesses"] if biz["business_id"] == business_id
            )
            return Business.model_validate(updated_business)

        # A concurrent request may have completed this key after our initial read.
        current_document = await collection.find_one({"player_id": player_id})
        if current_document is None:
            raise NotFoundError("Player", player_id)
        current_businesses = [
            Business.model_validate(item) for item in current_document["businesses"]
        ]
        current_business = next(
            (biz for biz in current_businesses if biz.business_id == business_id), None
        )
        if current_business is None:
            raise NotFoundError("Business", business_id)
        current_schedule = current_business.delivery_schedule
        if idempotency_key in current_schedule.processed_express_delivery_keys:
            return current_business
        if not current_schedule.is_active:
            raise InvalidOperationError("Delivery system is disabled for this business")
        PlayerValidator.validate_can_purchase(
            SimpleNamespace(money=current_document["money"]),
            current_schedule.express_delivery_cost,
        )
        raise InvalidOperationError("Express delivery was not applied; retry with the same key")
