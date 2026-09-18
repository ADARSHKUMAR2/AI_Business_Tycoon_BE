from typing import List
from services.game.models.business import Business, BusinessCreate
from services.game.models.player import PlayerState
from services.game.models.inventory import InventoryItem, InventoryUpdate, PriceUpdate
from services.game.models.land import LandType, Position
from services.game.config.settings import game_settings
from services.game.utils.state_manager import state_manager
from services.game.validators.business_validator import BusinessValidator
from services.game.validators.player_validator import PlayerValidator
from shared.exceptions import NotFoundError, InvalidOperationError

class BusinessController:
    """Controller for business-related logic."""
    
    @staticmethod
    async def create_business(data: BusinessCreate) -> Business:
        """Create a new business for a player."""
        BusinessValidator.validate_business_name(data.name)
        
        player = await state_manager.load_player(data.player_id)
        pos = Position(x=data.position_x, y=data.position_y)
        
        BusinessValidator.validate_business_position(player, pos)
        
        # Determine cost and inventory based on business type
        build_cost = game_settings.kirana_build_cost
        inventory_source = game_settings.default_inventory_items
        
        if data.business_type == "pizza":
            build_cost = game_settings.pizza_build_cost
            inventory_source = game_settings.pizza_inventory_items
        elif data.business_type == "cafe":
            build_cost = game_settings.cafe_build_cost
            inventory_source = game_settings.cafe_inventory_items
            
        PlayerValidator.validate_can_purchase(player, build_cost)
        
        # Deduct money
        player.deduct_money(build_cost)
        player.stats.total_expenses += build_cost
        
        # Convert default inventory dict to InventoryItem objects
        inventory_items = {
            key: InventoryItem(**item_data) 
            for key, item_data in inventory_source.items()
        }
        
        # Create business
        business = Business(
            player_id=player.player_id,
            business_type=data.business_type,
            name=data.name,
            position_x=data.position_x,
            position_y=data.position_y,
            inventory=inventory_items
        )
        
        # Update land tile type
        for tile in player.land_tiles:
            if tile.position == pos:
                tile.tile_type = LandType.SHOP
                tile.business_id = business.business_id
                break
                
        # Add to player and save
        player.businesses.append(business)
        player.stats.businesses_owned += 1
        await state_manager.save_player(player)
        
        return business

    @staticmethod
    async def _find_business_in_player(player: PlayerState, business_id: str) -> tuple[int, Business]:
        """Helper to find a business and its index."""
        for idx, biz in enumerate(player.businesses):
            if biz.business_id == business_id:
                return idx, biz
        raise NotFoundError("Business", business_id)

    @staticmethod
    async def get_business(player_id: str, business_id: str) -> Business:
        """Get business details."""
        player = await state_manager.load_player(player_id)
        _, business = BusinessController._find_business_in_player(player, business_id)
        return business

    @staticmethod
    async def update_inventory(player_id: str, business_id: str, update: InventoryUpdate) -> Business:
        """Update inventory stock or price."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)
        
        BusinessValidator.validate_inventory_update(business, update.item_key)
        
        item = business.inventory[update.item_key]
        
        # Calculate cost if restocking
        if update.stock > item.stock:
            added_stock = update.stock - item.stock
            cost = added_stock * item.cost
            PlayerValidator.validate_can_purchase(player, cost)
            player.deduct_money(cost)
            player.stats.total_expenses += cost
            business.stats.total_expenses += cost
            
        # Update item
        item.stock = update.stock
        item.price = update.price
        
        # Save state
        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)
        
        return business

    @staticmethod
    async def set_price_multiplier(player_id: str, business_id: str, update: PriceUpdate) -> Business:
        """Update global price multiplier for the business."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)
        
        BusinessValidator.validate_price_multiplier(update.price_multiplier)
        business.price_multiplier = update.price_multiplier
        
        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)
        
        return business
        
    @staticmethod
    async def toggle_business_status(player_id: str, business_id: str, is_open: bool) -> Business:
        """Open or close the business."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)
        
        business.is_open = is_open
        business.update_timestamp()
        
        player.businesses[idx] = business
        await state_manager.save_player(player)
        return business
