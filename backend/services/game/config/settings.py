"""
Game configuration and settings.
"""
from pydantic_settings import BaseSettings
from typing import Dict


class GameSettings(BaseSettings):
    """Game-specific settings loaded from environment."""
    
    # Starting configuration
    starting_money: float = 10000.0
    starting_land_size: int = 1
    
    # Business costs
    kirana_build_cost: float = 5000.0
    land_tile_base_cost: float = 2000.0
    
    # Employee configuration
    default_cashier_salary_min: float = 1000.0
    default_cashier_salary_max: float = 2000.0
    
    # Customer configuration
    customer_spawn_interval: int = 5
    customer_base_budget: float = 100.0
    
    # Inventory defaults for Kirana Store
    default_inventory_items: Dict[str, dict] = {
        "rice": {"name": "Rice (1kg)", "cost": 40, "price": 50, "stock": 100},
        "dal": {"name": "Dal (1kg)", "cost": 80, "price": 100, "stock": 50},
        "milk": {"name": "Milk (1L)", "cost": 50, "price": 60, "stock": 30},
        "bread": {"name": "Bread", "cost": 25, "price": 35, "stock": 40},
        "oil": {"name": "Cooking Oil (1L)", "cost": 120, "price": 150, "stock": 20},
        "sugar": {"name": "Sugar (1kg)", "cost": 35, "price": 45, "stock": 60},
        "salt": {"name": "Salt (1kg)", "cost": 15, "price": 20, "stock": 80},
        "tea": {"name": "Tea (250g)", "cost": 60, "price": 75, "stock": 40},
    }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global game settings instance
game_settings = GameSettings()
