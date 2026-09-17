"""
Customer generator for creating NPC customers.
"""
import random
from typing import List

from services.game.models.customer import Customer
from services.game.config.constants import (
    CUSTOMER_MIN_PATIENCE,
    CUSTOMER_MAX_PATIENCE,
    CUSTOMER_MIN_BUDGET,
    CUSTOMER_MAX_BUDGET,
)
from services.game.config.settings import game_settings


class CustomerGenerator:
    """Generates customers for business simulation."""
    
    @staticmethod
    def generate_random_budget(base_budget: float = None) -> float:
        """Generate random customer budget."""
        if base_budget is None:
            base_budget = game_settings.customer_base_budget
        
        # Budget varies ±50% around base
        min_budget = max(CUSTOMER_MIN_BUDGET, base_budget * 0.5)
        max_budget = min(CUSTOMER_MAX_BUDGET, base_budget * 1.5)
        
        return round(random.uniform(min_budget, max_budget), 2)
    
    @staticmethod
    def generate_random_patience() -> int:
        """Generate random patience in seconds."""
        return random.randint(CUSTOMER_MIN_PATIENCE, CUSTOMER_MAX_PATIENCE)
    
    @staticmethod
    def generate_shopping_list(available_items: List[str], budget: float, item_prices: dict) -> List[str]:
        """
        Generate a shopping list based on budget and available items.
        
        Args:
            available_items: List of item keys available in the store
            budget: Customer's budget
            item_prices: Dict mapping item keys to prices
            
        Returns:
            List of item keys customer wants to buy
        """
        shopping_list = []
        remaining_budget = budget
        
        # Shuffle items for variety
        shuffled_items = random.sample(available_items, len(available_items))
        
        # Add items until budget is exhausted or we have 1-5 items
        max_items = random.randint(1, 5)
        for item_key in shuffled_items:
            if len(shopping_list) >= max_items:
                break
            
            price = item_prices.get(item_key, 0)
            if price > 0 and price <= remaining_budget:
                shopping_list.append(item_key)
                remaining_budget -= price
        
        return shopping_list
    
    @classmethod
    def generate_customer(
        cls,
        business_id: str,
        available_items: List[str],
        item_prices: dict
    ) -> Customer:
        """
        Generate a customer for a specific business.
        
        Args:
            business_id: Target business ID
            available_items: Items available in the business
            item_prices: Prices of items
            
        Returns:
            Customer instance
        """
        budget = cls.generate_random_budget()
        patience = cls.generate_random_patience()
        shopping_list = cls.generate_shopping_list(available_items, budget, item_prices)
        
        return Customer(
            budget=budget,
            patience=patience,
            items_to_buy=shopping_list,
            business_id=business_id
        )
