"""
Inventory models for business stock management.
"""
from pydantic import BaseModel, Field
from typing import Dict


class InventoryItem(BaseModel):
    """Single inventory item in a business."""
    name: str = Field(..., description="Display name of the item")
    cost: float = Field(..., gt=0, description="Cost price per unit")
    price: float = Field(..., gt=0, description="Selling price per unit")
    stock: int = Field(..., ge=0, description="Current stock quantity")
    total_sold: int = Field(0, ge=0, description="Total units sold")
    
    def calculate_profit_per_unit(self) -> float:
        """Calculate profit per unit."""
        return self.price - self.cost
    
    def calculate_total_profit(self) -> float:
        """Calculate total profit from sold items."""
        return self.total_sold * self.calculate_profit_per_unit()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Rice (1kg)",
                "cost": 40.0,
                "price": 50.0,
                "stock": 100,
                "total_sold": 0
            }
        }
    }


class InventoryUpdate(BaseModel):
    """Update inventory for a business."""
    item_key: str = Field(..., description="Item identifier (e.g., 'rice')")
    stock: int = Field(..., ge=0, description="New stock quantity")
    price: float = Field(..., gt=0, description="New selling price")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "item_key": "rice",
                "stock": 150,
                "price": 55.0
            }
        }
    }


class PriceUpdate(BaseModel):
    """Update prices for business items."""
    price_multiplier: float = Field(..., gt=0, le=3.0, description="Price multiplier (0.5 to 3.0)")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "price_multiplier": 1.2
            }
        }
    }
