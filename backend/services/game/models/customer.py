"""
Customer models for simulation (Phase 1 - basic).
"""
from pydantic import BaseModel, Field
from enum import Enum
from typing import List
import uuid


class CustomerStatus(str, Enum):
    """Customer states in simulation."""
    SPAWNED = "spawned"
    WALKING = "walking"
    QUEUED = "queued"
    BUYING = "buying"
    LEAVING = "leaving"
    LEFT = "left"


class Customer(BaseModel):
    """Customer model for simulation."""
    customer_id: str = Field(default_factory=lambda: f"cust_{uuid.uuid4().hex[:8]}")
    budget: float = Field(..., gt=0, description="Customer's budget in ₹")
    patience: int = Field(..., ge=10, le=300, description="Patience in seconds")
    items_to_buy: List[str] = Field(default_factory=list, description="List of item keys")
    status: CustomerStatus = CustomerStatus.SPAWNED
    business_id: str = Field(..., description="Target business ID")
    
    def has_budget_for(self, price: float) -> bool:
        """Check if customer can afford an item."""
        return self.budget >= price
    
    def purchase(self, price: float) -> bool:
        """Process a purchase. Returns True if successful."""
        if self.has_budget_for(price):
            self.budget -= price
            return True
        return False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "customer_id": "cust_xyz789",
                "budget": 150.0,
                "patience": 60,
                "items_to_buy": ["rice", "milk", "bread"],
                "status": "spawned",
                "business_id": "biz_abc123"
            }
        }
    }
