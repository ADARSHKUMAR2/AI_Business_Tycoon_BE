"""
Land and position models for the game grid system.
"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class LandType(str, Enum):
    """Types of land tiles."""
    EMPTY = "empty"
    SHOP = "shop"
    ROAD = "road"
    PARKING = "parking"


class Position(BaseModel):
    """2D position on the grid."""
    x: int = Field(..., description="X coordinate")
    y: int = Field(..., description="Y coordinate")
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __eq__(self, other):
        if isinstance(other, Position):
            return self.x == other.x and self.y == other.y
        return False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "x": 0,
                "y": 0
            }
        }
    }


class LandTile(BaseModel):
    """Represents a single land tile."""
    position: Position
    tile_type: LandType = LandType.EMPTY
    purchase_cost: float = Field(..., ge=0, description="Cost to purchase this tile")
    purchased_at: datetime = Field(default_factory=datetime.utcnow)
    business_id: Optional[str] = Field(None, description="ID of business built on this tile")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "position": {"x": 0, "y": 0},
                "tile_type": "empty",
                "purchase_cost": 2000.0,
                "purchased_at": "2026-09-17T08:00:00Z",
                "business_id": None
            }
        }
    }


class LandPurchaseRequest(BaseModel):
    """Request to purchase a land tile."""
    player_id: str = Field(..., description="Player ID")
    position: Position = Field(..., description="Position to purchase")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "player_id": "player_123",
                "position": {"x": 1, "y": 0}
            }
        }
    }
