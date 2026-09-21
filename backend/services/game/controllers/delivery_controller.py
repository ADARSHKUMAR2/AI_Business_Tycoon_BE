"""
Delivery controller for Phase 4 Feature 3.
Handles timed supply events and express restock purchases.
"""

from datetime import datetime, timedelta
from typing import Optional

from services.game.models.business import Business
from services.game.models.delivery import DeliveryStatusResponse
from services.game.models.player import PlayerState
from services.game.utils.state_manager import state_manager
from services.game.validators.player_validator import PlayerValidator
from shared.exceptions import NotFoundError, InvalidOperationError


class DeliveryController:
    """Manage supply truck deliveries for businesses."""

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
        - If the current time exceeds next_delivery_at, trigger a truck arrival
        - Restock all inventory items to max_stock
        - Move next delivery forward by interval
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
            for item in business.inventory.values():
                item.stock = item.max_stock

            schedule.last_delivery_at = current
            schedule.next_delivery_at = current + timedelta(minutes=schedule.delivery_interval_minutes)

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
        for item in business.inventory.values():
            item.stock = item.max_stock

        schedule.mark_delivered(now)
        business.last_updated = now
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    @staticmethod
    async def request_express_delivery(player_id: str, business_id: str) -> Business:
        """
        Player pays a fee to trigger an immediate delivery.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await DeliveryController._find_business_in_player(player, business_id)

        schedule = business.delivery_schedule
        if not schedule.is_active:
            raise InvalidOperationError("Delivery system is disabled for this business")

        cost = schedule.express_delivery_cost
        PlayerValidator.validate_can_purchase(player, cost)

        player.deduct_money(cost)
        player.stats.total_expenses += cost

        now = datetime.utcnow()
        for item in business.inventory.values():
            item.stock = item.max_stock

        schedule.mark_delivered(now)
        business.last_updated = now
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business
