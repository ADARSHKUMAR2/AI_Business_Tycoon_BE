from typing import List
from services.game.models.land import LandPurchaseRequest, LandTile, LandType, Position
from services.game.utils.state_manager import state_manager
from services.game.utils.economy_calculator import EconomyCalculator
from services.game.validators.player_validator import PlayerValidator
from services.game.utils.helpers import GameHelpers

class LandController:
    """Controller for land expansion."""

    @staticmethod
    async def get_available_land(player_id: str) -> List[dict]:
        """Calculate and return available adjacent tiles with prices."""
        player = await state_manager.load_player(player_id)
        
        owned_positions = {tile.position for tile in player.land_tiles}
        available_tiles = []
        
        # Calculate next tile cost
        current_tiles_count = len(player.land_tiles)
        next_cost = EconomyCalculator.calculate_land_cost(current_tiles_count)
        
        # Find all valid adjacent positions
        for tile in player.land_tiles:
            adjacent_pos_list = GameHelpers.get_adjacent_positions(tile.position.x, tile.position.y)
            
            for px, py in adjacent_pos_list:
                pos = Position(x=px, y=py)
                
                # Check grid bounds and not already owned
                if GameHelpers.is_valid_grid_position(px, py) and pos not in owned_positions:
                    # Avoid duplicates in available_tiles
                    if not any(t["position"]["x"] == px and t["position"]["y"] == py for t in available_tiles):
                        available_tiles.append({
                            "position": {"x": px, "y": py},
                            "cost": next_cost,
                            "can_afford": player.money >= next_cost
                        })
                        
        return available_tiles

    @staticmethod
    async def purchase_land(request: LandPurchaseRequest) -> LandTile:
        """Purchase a new land tile."""
        player = await state_manager.load_player(request.player_id)
        
        PlayerValidator.validate_land_position(player, request.position)
        
        current_tiles_count = len(player.land_tiles)
        cost = EconomyCalculator.calculate_land_cost(current_tiles_count)
        
        PlayerValidator.validate_can_purchase(player, cost)
        
        # Deduct money
        player.deduct_money(cost)
        
        # Create tile
        new_tile = LandTile(
            position=request.position,
            tile_type=LandType.EMPTY,
            purchase_cost=cost
        )
        
        # Add to player
        player.land_tiles.append(new_tile)
        player.stats.land_tiles_owned += 1
        
        # Save
        await state_manager.save_player(player)
        return new_tile
