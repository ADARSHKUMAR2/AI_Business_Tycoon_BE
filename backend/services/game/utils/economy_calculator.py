"""
Economy calculations and formulas.
"""
from typing import Dict, List
from services.game.models.business import Business
from services.game.models.player import PlayerState
from services.game.models.inventory import InventoryItem


class EconomyCalculator:
    """Handles economic calculations for the game."""
    
    @staticmethod
    def calculate_land_cost(current_tiles: int, base_cost: float = 2000.0) -> float:
        """
        Calculate cost of next land tile (increases with each purchase).
        
        Args:
            current_tiles: Number of tiles already owned
            base_cost: Base cost of first tile
            
        Returns:
            Cost of next tile
        """
        # Cost increases by 20% for each tile
        multiplier = 1.2 ** current_tiles
        return round(base_cost * multiplier, 2)
    
    @staticmethod
    def calculate_restocking_cost(inventory: Dict[str, InventoryItem], restock_to: int = 100) -> float:
        """
        Calculate cost to restock all inventory items.
        
        Args:
            inventory: Current inventory
            restock_to: Target stock level
            
        Returns:
            Total restocking cost
        """
        total_cost = 0.0
        for item in inventory.values():
            needed = max(0, restock_to - item.stock)
            total_cost += needed * item.cost
        return total_cost
    
    @staticmethod
    def calculate_item_profit_margin(item: InventoryItem) -> float:
        """Calculate profit margin percentage for an item."""
        if item.cost == 0:
            return 0.0
        return ((item.price - item.cost) / item.cost) * 100
    
    @staticmethod
    def calculate_business_roi(business: Business) -> float:
        """
        Calculate Return on Investment for a business.
        
        Args:
            business: Business instance
            
        Returns:
            ROI percentage
        """
        initial_investment = 5000.0  # Kirana build cost
        profit = business.stats.calculate_profit()
        
        if initial_investment == 0:
            return 0.0
        
        return (profit / initial_investment) * 100
    
    @staticmethod
    def calculate_break_even_sales(business: Business) -> float:
        """
        Calculate sales needed to break even.
        
        Args:
            business: Business instance
            
        Returns:
            Amount needed to break even
        """
        expenses = business.stats.total_expenses
        revenue = business.stats.total_revenue
        
        if revenue >= expenses:
            return 0.0  # Already profitable
        
        return expenses - revenue
    
    @staticmethod
    def simulate_daily_revenue(
        business: Business,
        customers_per_day: int = 50,
        avg_items_per_customer: int = 3
    ) -> float:
        """
        Estimate daily revenue based on customer traffic.
        
        Args:
            business: Business instance
            customers_per_day: Expected customers
            avg_items_per_customer: Average items per customer
            
        Returns:
            Estimated daily revenue
        """
        if not business.inventory:
            return 0.0
        
        # Calculate average item price
        total_price = sum(item.price for item in business.inventory.values())
        avg_price = total_price / len(business.inventory)
        
        # Estimate revenue
        estimated_revenue = customers_per_day * avg_items_per_customer * avg_price * business.price_multiplier
        
        return round(estimated_revenue, 2)
    
    @staticmethod
    def calculate_optimal_price(cost: float, target_margin: float = 0.25) -> float:
        """
        Calculate optimal selling price based on cost and target margin.
        
        Args:
            cost: Item cost
            target_margin: Target profit margin (0.25 = 25%)
            
        Returns:
            Optimal price
        """
        return round(cost * (1 + target_margin), 2)
