"""
State manager for JSON-based persistence (Phase 1).
"""
import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from services.game.models.player import PlayerState
from shared.exceptions import NotFoundError, StateManagerError, AlreadyExistsError


class StateManager:
    """Manages player state persistence using JSON files."""
    
    def __init__(self, data_dir: str = "./data"):
        """
        Initialize state manager.
        
        Args:
            data_dir: Directory for storing JSON files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_player_file_path(self, player_id: str) -> Path:
        """Get file path for player data."""
        return self.data_dir / f"{player_id}.json"
    
    def player_exists(self, player_id: str) -> bool:
        """Check if player exists."""
        return self._get_player_file_path(player_id).exists()
    
    def save_player(self, player: PlayerState) -> None:
        """
        Save player state to JSON file.
        
        Args:
            player: Player state to save
            
        Raises:
            StateManagerError: If save fails
        """
        try:
            file_path = self._get_player_file_path(player.player_id)
            
            # Update timestamp
            player.update_timestamp()
            
            # Convert to dict and handle datetime serialization
            player_dict = player.model_dump(mode='json')
            
            # Write to file with pretty formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(player_dict, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise StateManagerError(f"Failed to save player {player.player_id}: {str(e)}")
    
    def load_player(self, player_id: str) -> PlayerState:
        """
        Load player state from JSON file.
        
        Args:
            player_id: Player ID to load
            
        Returns:
            Player state
            
        Raises:
            NotFoundError: If player not found
            StateManagerError: If load fails
        """
        if not self.player_exists(player_id):
            raise NotFoundError("Player", player_id)
        
        try:
            file_path = self._get_player_file_path(player_id)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                player_dict = json.load(f)
            
            # Parse back to PlayerState
            player = PlayerState(**player_dict)
            
            # Update last login
            player.update_login()
            
            return player
            
        except NotFoundError:
            raise
        except Exception as e:
            raise StateManagerError(f"Failed to load player {player_id}: {str(e)}")
    
    def delete_player(self, player_id: str) -> None:
        """
        Delete player data.
        
        Args:
            player_id: Player ID to delete
            
        Raises:
            NotFoundError: If player not found
            StateManagerError: If delete fails
        """
        if not self.player_exists(player_id):
            raise NotFoundError("Player", player_id)
        
        try:
            file_path = self._get_player_file_path(player_id)
            file_path.unlink()
        except Exception as e:
            raise StateManagerError(f"Failed to delete player {player_id}: {str(e)}")
    
    def list_all_players(self) -> List[str]:
        """
        List all player IDs.
        
        Returns:
            List of player IDs
        """
        try:
            json_files = self.data_dir.glob("*.json")
            return [f.stem for f in json_files]
        except Exception as e:
            raise StateManagerError(f"Failed to list players: {str(e)}")
    
    def get_player_count(self) -> int:
        """Get total number of players."""
        return len(self.list_all_players())


# Global state manager instance
state_manager = StateManager()
