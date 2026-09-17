from typing import List
from services.game.models.player import PlayerState, PlayerCreate, PlayerUpdate
from services.game.models.land import LandTile, LandType, Position
from services.game.config.settings import game_settings
from services.game.utils.state_manager import state_manager
from services.game.validators.player_validator import PlayerValidator
from shared.exceptions import NotFoundError, AlreadyExistsError

class PlayerController:
    """Controller for player-related business logic."""
    
    @staticmethod
    def create_player(player_data: PlayerCreate) -> PlayerState:
        """Create a new player with starting assets."""
        PlayerValidator.validate_player_name(player_data.name)
        
        # Create starting land tile (at origin 0,0)
        starting_land = LandTile(
            position=Position(x=0, y=0),
            tile_type=LandType.EMPTY,
            purchase_cost=0.0  # Free starting land
        )
        
        # Create player state
        player = PlayerState(
            name=player_data.name,
            money=game_settings.starting_money,
            land_tiles=[starting_land]
        )
        
        # Initial stats setup
        player.stats.land_tiles_owned = 1
        
        # Check if already exists (highly unlikely with UUID)
        if state_manager.player_exists(player.player_id):
            raise AlreadyExistsError("Player", player.player_id)
            
        state_manager.save_player(player)
        return player

    @staticmethod
    def get_player(player_id: str) -> PlayerState:
        """Get player by ID."""
        return state_manager.load_player(player_id)

    @staticmethod
    def update_player(player_id: str, update_data: PlayerUpdate) -> PlayerState:
        """Update player details."""
        player = state_manager.load_player(player_id)
        
        if update_data.name is not None:
            PlayerValidator.validate_player_name(update_data.name)
            player.name = update_data.name
            
        if update_data.money is not None:
            PlayerValidator.validate_money_amount(update_data.money)
            player.money = update_data.money
            
        state_manager.save_player(player)
        return player

    @staticmethod
    def delete_player(player_id: str) -> dict:
        """Delete a player."""
        state_manager.delete_player(player_id)
        return {"message": f"Player {player_id} deleted successfully"}
        
    @staticmethod
    def get_all_players() -> List[str]:
        """List all player IDs."""
        return state_manager.list_all_players()
