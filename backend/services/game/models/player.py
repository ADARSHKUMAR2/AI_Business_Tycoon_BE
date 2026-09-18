"""
Player models for game state management.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
import uuid

from .land import LandTile, Position
from .business import Business
from beanie import Document

class PlayerCreate(BaseModel):
    """Schema for creating a new player."""
    name: str = Field(..., min_length=2, max_length=50, description="Player name")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Adarsh"
            }
        }
    }


class PlayerUpdate(BaseModel):
    """Schema for updating player data."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    money: Optional[float] = Field(None, ge=0)
    stats: Optional[PlayerStats] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Adarsh Kumar",
                "money": 15000.0,
                "stats": {
                    "total_revenue": 5000.0,
                    "total_expenses": 2000.0,
                    "businesses_owned": 1,
                    "employees_hired": 0,
                    "land_tiles_owned": 1,
                    "level": 2,
                    "experience": 150
                }
            }
        }
    }


class PlayerStats(BaseModel):
    """Player statistics and progression."""
    total_revenue: float = Field(0.0, ge=0, description="Lifetime revenue")
    total_expenses: float = Field(0.0, ge=0, description="Lifetime expenses")
    businesses_owned: int = Field(0, ge=0, description="Number of businesses owned")
    employees_hired: int = Field(0, ge=0, description="Total employees hired")
    land_tiles_owned: int = Field(0, ge=0, description="Number of land tiles owned")
    level: int = Field(1, ge=1, description="Player level")
    experience: int = Field(0, ge=0, description="Experience points")
    
    def calculate_net_profit(self) -> float:
        """Calculate net profit."""
        return self.total_revenue - self.total_expenses


class PlayerState(Document):
    """Complete player state."""
    player_id: str = Field(default_factory=lambda: f"player_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=2, max_length=50)
    money: float = Field(..., ge=0, description="Current money in ₹")
    land_tiles: List[LandTile] = Field(default_factory=list)
    businesses: List[Business] = Field(default_factory=list)
    stats: PlayerStats = Field(default_factory=PlayerStats)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    # We must define Settings for Beanie
    class Settings:
        name = "players"
    
    def calculate_net_worth(self) -> float:
        """Calculate total net worth (money + business value + land value)."""
        business_value = sum(biz.calculate_business_value() for biz in self.businesses)
        land_value = sum(tile.purchase_cost for tile in self.land_tiles)
        return self.money + business_value + land_value
    
    def calculate_daily_income(self) -> float:
        """Calculate total daily income from all businesses."""
        # Simplified calculation for Phase 1
        total_revenue = sum(biz.stats.total_revenue for biz in self.businesses)
        days_active = max(1, (datetime.utcnow() - self.created_at).days)
        return total_revenue / days_active if days_active > 0 else 0.0
    
    def calculate_daily_expenses(self) -> float:
        """Calculate total daily expenses from all businesses."""
        return sum(biz.calculate_daily_expenses() for biz in self.businesses)
    
    def has_land_at(self, position: Position) -> bool:
        """Check if player owns land at given position."""
        return any(tile.position == position for tile in self.land_tiles)
    
    def get_business_at(self, position: Position) -> Optional[Business]:
        """Get business at given position."""
        for business in self.businesses:
            if business.position_x == position.x and business.position_y == position.y:
                return business
        return None
    
    def add_money(self, amount: float):
        """Add money to player."""
        self.money += amount
        self.update_timestamp()
    
    def deduct_money(self, amount: float) -> bool:
        """Deduct money from player. Returns False if insufficient funds."""
        if self.money >= amount:
            self.money -= amount
            self.update_timestamp()
            return True
        return False
    
    def update_timestamp(self):
        """Update last_updated timestamp."""
        self.last_updated = datetime.utcnow()
    
    def update_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "player_id": "player_a1b2c3d4",
                "name": "Adarsh",
                "money": 10000.0,
                "land_tiles": [
                    {
                        "position": {"x": 0, "y": 0},
                        "tile_type": "empty",
                        "purchase_cost": 0.0,
                        "purchased_at": "2026-09-17T08:00:00Z",
                        "business_id": None
                    }
                ],
                "businesses": [],
                "stats": {
                    "total_revenue": 0.0,
                    "total_expenses": 0.0,
                    "businesses_owned": 0,
                    "employees_hired": 0,
                    "land_tiles_owned": 1,
                    "level": 1,
                    "experience": 0
                },
                "created_at": "2026-09-17T08:00:00Z",
                "last_login": "2026-09-17T08:00:00Z",
                "last_updated": "2026-09-17T08:00:00Z"
            }
        }
    }
