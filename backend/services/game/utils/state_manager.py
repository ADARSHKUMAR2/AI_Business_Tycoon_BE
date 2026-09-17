"""
State manager using MongoDB (via Beanie).
"""
from typing import List, Optional
from services.game.models.player import PlayerState
from shared.exceptions import NotFoundError, StateManagerError, AlreadyExistsError

class StateManager:
    """Manages player state persistence using MongoDB."""
    
    async def player_exists(self, player_id: str) -> bool:
        """Check if player exists."""
        player = await PlayerState.find_one(PlayerState.player_id == player_id)
        return player is not None
    
    async def save_player(self, player: PlayerState) -> None:
        """Save or update player state in MongoDB."""
        try:
            player.update_timestamp()
            # Beanie's .save() handles both inserts and updates automatically
            await player.save()
        except Exception as e:
            raise StateManagerError(f"Failed to save player {player.player_id}: {str(e)}")
    
    async def load_player(self, player_id: str) -> PlayerState:
        """Load player state from MongoDB."""
        player = await PlayerState.find_one(PlayerState.player_id == player_id)
        if not player:
            raise NotFoundError("Player", player_id)
            
        try:
            player.update_login()
            await player.save()  # Save the updated login time
            return player
        except Exception as e:
            raise StateManagerError(f"Failed to load player {player_id}: {str(e)}")
    
    async def delete_player(self, player_id: str) -> None:
        """Delete player data from MongoDB."""
        player = await PlayerState.find_one(PlayerState.player_id == player_id)
        if not player:
            raise NotFoundError("Player", player_id)
        
        try:
            await player.delete()
        except Exception as e:
            raise StateManagerError(f"Failed to delete player {player_id}: {str(e)}")
    
    async def list_all_players(self) -> List[str]:
        """List all player IDs."""
        try:
            # Find all players and project only the player_id field
            players = await PlayerState.find_all().project(PlayerState.player_id).to_list()
            # The projection returns dictionaries for performance
            return [p["player_id"] for p in players if "player_id" in p]
        except Exception as e:
            raise StateManagerError(f"Failed to list players: {str(e)}")

# Global state manager instance
state_manager = StateManager()
