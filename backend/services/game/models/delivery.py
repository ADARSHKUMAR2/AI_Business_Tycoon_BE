"""
Delivery schedule models for Phase 4 Feature 3.
This keeps the server authoritative for stock restock timing.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class DeliverySchedule(BaseModel):
    """
    Scheduler embedded inside each business.

    Logic:
    - Truck arrives every N minutes
    - For a fixed supply window after arrival, stock is available
    - After that, no more supply is available until next scheduled arrival
    """
    delivery_interval_minutes: int = Field(
        5,
        ge=1,
        le=1440,
        description="How many minutes between restocks"
    )
    last_delivery_at: Optional[datetime] = Field(
        default=None,
        description="When the most recent truck arrived"
    )
    next_delivery_at: Optional[datetime] = Field(
        default=None,
        description="When the next truck is due"
    )
    supply_window_seconds: int = Field(
        90,
        ge=30,
        le=600,
        description="How long the supply zone stays active after delivery"
    )
    express_delivery_cost: float = Field(
        500.0,
        gt=0,
        description="Cost to trigger an immediate restock"
    )
    is_active: bool = Field(
        True,
        description="Whether delivery system is enabled for this business"
    )

    def mark_delivered(self, now: Optional[datetime] = None) -> None:
        """Set delivery time and schedule the next delivery."""
        current = now or datetime.utcnow()
        self.last_delivery_at = current
        self.next_delivery_at = current + timedelta(minutes=self.delivery_interval_minutes)

    def is_supply_available(self, now: Optional[datetime] = None) -> bool:
        """
        True if the business is currently in the active supply window.

        Example:
        - truck arrives at 12:00
        - supply active until 12:01:30
        - after that, no stock pickup
        """
        current = now or datetime.utcnow()
        if self.last_delivery_at is None:
            return False
        if not self.is_active:
            return False

        supply_end = self.last_delivery_at + timedelta(seconds=self.supply_window_seconds)
        return current < supply_end

    def seconds_until_next(self, now: Optional[datetime] = None) -> int:
        """
        Number of seconds until the next scheduled truck arrival.
        """
        if self.next_delivery_at is None:
            return 0
        current = now or datetime.utcnow()
        return max(0, int((self.next_delivery_at - current).total_seconds()))

    def seconds_until_supply_window_end(self, now: Optional[datetime] = None) -> int:
        """
        Remaining seconds in the current active supply window.
        """
        current = now or datetime.utcnow()
        if self.last_delivery_at is None:
            return 0
        if not self.is_supply_available(current):
            return 0
        supply_end = self.last_delivery_at + timedelta(seconds=self.supply_window_seconds)
        return max(0, int((supply_end - current).total_seconds()))


class DeliveryStatusResponse(BaseModel):
    """Response payload for GET /delivery/{player_id}/{business_id}/status."""
    business_id: str
    supply_available: bool
    seconds_until_next: int
    supply_window_remaining: int
    last_delivery_at: Optional[datetime]
    next_delivery_at: Optional[datetime]
    delivery_interval_minutes: int
    express_delivery_cost: float


class ExpressDeliveryRequest(BaseModel):
    """Optional future extension — currently not required for immediate logic."""
    pass
