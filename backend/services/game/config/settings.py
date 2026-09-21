"""
Game configuration and settings.
"""
from pydantic_settings import BaseSettings
from typing import Dict


class GameSettings(BaseSettings):
    """Game-specific settings loaded from environment."""

    # ── Database configuration ────────────────────────────────────────
    mongodb_uri:     str = "mongodb://localhost:27017/"
    mongodb_db_name: str = "ai_business_tycoon"

    # ── Starting configuration ────────────────────────────────────────
    starting_money:     float = 10000.0
    starting_land_size: int   = 1

    # ── Business build costs ──────────────────────────────────────────
    kirana_build_cost:    float = 5000.0
    pizza_build_cost:     float = 15000.0
    cafe_build_cost:      float = 25000.0
    land_tile_base_cost:  float = 2000.0

    # ── Employee salary ranges ────────────────────────────────────────
    default_cashier_salary_min:  float = 1000.0
    default_cashier_salary_max:  float = 2000.0

    # Phase 3: Cleaner is cheaper to hire than a cashier/restocker
    default_cleaner_salary_min:  float = 600.0
    default_cleaner_salary_max:  float = 1200.0

    # ── Customer configuration ────────────────────────────────────────
    customer_spawn_interval: int   = 5
    customer_base_budget:    float = 100.0

    # ── Business build costs ──────────────────────────────────────────
    kirana_build_cost:    float = 5000.0
    pizza_build_cost:     float = 15000.0
    cafe_build_cost:      float = 25000.0
    land_tile_base_cost:  float = 2000.0

    # ── NEW: Employee Hire Costs (Can be overridden in .env) ──────────
    cashier_hire_cost:    float = 1000.0
    restocker_hire_cost:  float = 1500.0
    cleaner_hire_cost:    float = 800.0

    # ── Employee salary ranges ────────────────────────────────────────
    default_cashier_salary_min:  float = 1000.0
    default_cashier_salary_max:  float = 2000.0


    # ── Inventory defaults for Kirana Store ───────────────────────────
    default_inventory_items: Dict[str, dict] = {
        "rice":  {"name": "Rice (1kg)",        "cost": 40,  "price": 50,  "stock": 10},
        "dal":   {"name": "Dal (1kg)",          "cost": 80,  "price": 100, "stock": 10},
        "milk":  {"name": "Milk (1L)",          "cost": 50,  "price": 60,  "stock": 10},
        "bread": {"name": "Bread",              "cost": 25,  "price": 35,  "stock": 10},
        "oil":   {"name": "Cooking Oil (1L)",   "cost": 120, "price": 150, "stock": 10},
        "sugar": {"name": "Sugar (1kg)",        "cost": 35,  "price": 45,  "stock": 10},
        "salt":  {"name": "Salt (1kg)",         "cost": 15,  "price": 20,  "stock": 10},
        "tea":   {"name": "Tea (250g)",         "cost": 60,  "price": 75,  "stock": 10},
    }

    # ── Inventory defaults for Pizza Outlet ───────────────────────────
    pizza_inventory_items: Dict[str, dict] = {
        "margherita":  {"name": "Margherita Pizza", "cost": 120, "price": 250, "stock": 10},
        "pepperoni":   {"name": "Pepperoni Pizza",  "cost": 180, "price": 350, "stock": 10},
        "garlic_bread":{"name": "Garlic Bread",     "cost": 50,  "price": 120, "stock": 10},
        "cola":        {"name": "Cola (500ml)",      "cost": 30,  "price": 60,  "stock": 10},
    }

    # ── Inventory defaults for Cafe ───────────────────────────────────
    cafe_inventory_items: Dict[str, dict] = {
        "espresso":   {"name": "Espresso",          "cost": 40, "price": 120, "stock": 10},
        "cappuccino": {"name": "Cappuccino",         "cost": 60, "price": 180, "stock": 10},
        "croissant":  {"name": "Butter Croissant",   "cost": 45, "price": 110, "stock": 10},
        "muffin":     {"name": "Blueberry Muffin",   "cost": 50, "price": 130, "stock": 10},
    }

    # ── Phase 4: Supply delivery settings ──────────────────────────────
    delivery_interval_minutes: int = 5
    supply_window_seconds: int = 90
    express_delivery_cost: float = 500.0

    class Config:
        env_file       = ".env"
        case_sensitive = False
        extra          = "ignore"


# Global game settings instance
game_settings = GameSettings()
