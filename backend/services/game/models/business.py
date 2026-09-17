"""
Business models for shop management.
"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from .inventory import InventoryItem
from .employee import Employee


class BusinessType(str, Enum):
    """Types of businesses available."""
    KIRANA = "kirana"
    # Future: PIZZA = "pizza", CAFE = "cafe", etc.


class BusinessStats(BaseModel):
    """Business performance statistics."""
    total_revenue: float = Field(0.0, ge=0, description="Total revenue earned")
    total_expenses: float = Field(0.0, ge=0, description="Total expenses incurred")
    total_customers_served: int = Field(0, ge=0, description="Total customers served")
    average_transaction: float = Field(0.0, ge=0, description="Average transaction value")
    
    def calculate_profit(self) -> float:
        """Calculate total profit."""
        return self.total_revenue - self.total_expenses
    
    def calculate_profit_margin(self) -> float:
        """Calculate profit margin percentage."""
        if self.total_revenue == 0:
            return 0.0
        return (self.calculate_profit() / self.total_revenue) * 100


class BusinessCreate(BaseModel):
    """Schema for creating a new business."""
    player_id: str = Field(..., description="Owner's player ID")
    business_type: BusinessType = BusinessType.KIRANA
    name: str = Field(..., min_length=2, max_length=100, description="Business name")
    position_x: int = Field(..., description="X position on grid")
    position_y: int = Field(..., description="Y position on grid")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "player_id": "player_123",
                "business_type": "kirana",
                "name": "Ravi's Kirana Store",
                "position_x": 0,
                "position_y": 0
            }
        }
    }


class Business(BaseModel):
    """Business model with full state."""
    business_id: str = Field(default_factory=lambda: f"biz_{uuid.uuid4().hex[:8]}")
    player_id: str = Field(..., description="Owner's player ID")
    business_type: BusinessType
    name: str = Field(..., min_length=2, max_length=100)
    position_x: int
    position_y: int
    inventory: Dict[str, InventoryItem] = Field(default_factory=dict)
    employees: List[Employee] = Field(default_factory=list)
    price_multiplier: float = Field(1.0, gt=0, le=3.0, description="Global price multiplier")
    is_open: bool = Field(True, description="Whether business is open")
    stats: BusinessStats = Field(default_factory=BusinessStats)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_daily_expenses(self) -> float:
        """Calculate daily operating expenses."""
        employee_salaries = sum(emp.salary_per_day for emp in self.employees)
        rent = 500.0  # Base rent
        electricity = 200.0  # Base electricity
        return employee_salaries + rent + electricity
    
    def calculate_inventory_value(self) -> float:
        """Calculate total inventory value (at cost)."""
        return sum(item.cost * item.stock for item in self.inventory.values())
    
    def calculate_business_value(self) -> float:
        """Calculate total business value."""
        inventory_value = self.calculate_inventory_value()
        # Business goodwill = total profit / 10
        goodwill = self.stats.calculate_profit() / 10
        return inventory_value + goodwill + 5000  # Base business value
    
    def get_employee_count(self) -> int:
        """Get number of employees."""
        return len(self.employees)
    
    def update_timestamp(self):
        """Update last_updated timestamp."""
        self.last_updated = datetime.utcnow()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "business_id": "biz_abc12345",
                "player_id": "player_123",
                "business_type": "kirana",
                "name": "Ravi's Kirana Store",
                "position_x": 0,
                "position_y": 0,
                "inventory": {
                    "rice": {
                        "name": "Rice (1kg)",
                        "cost": 40.0,
                        "price": 50.0,
                        "stock": 100,
                        "total_sold": 0
                    }
                },
                "employees": [],
                "price_multiplier": 1.0,
                "is_open": True,
                "stats": {
                    "total_revenue": 0.0,
                    "total_expenses": 0.0,
                    "total_customers_served": 0,
                    "average_transaction": 0.0
                },
                "created_at": "2026-09-17T08:00:00Z",
                "last_updated": "2026-09-17T08:00:00Z"
            }
        }
    }
