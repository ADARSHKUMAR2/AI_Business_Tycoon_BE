"""
Player data validators.
"""
from typing import Optional
from services.game.models.player import PlayerState, PlayerCreate
from services.game.models.land import Position
from shared.exceptions import ValidationError


class PlayerValidator:
    """Validates player-related operations."""
    
    @staticmethod
    def validate_player_name(name: str) -> None:
        """
        Validate player name.
        
        Raises:
            ValidationError: If name is invalid
        """
        if not name or len(name.strip()) < 2:
            raise ValidationError("Player name must be at least 2 characters", field="name")
        
        if len(name) > 50:
            raise ValidationError("Player name must not exceed 50 characters", field="name")
        
        # Check for invalid characters
        if not name.replace(" ", "").isalnum():
            raise ValidationError("Player name can only contain letters, numbers, and spaces", field="name")
    
    @staticmethod
    def validate_money_amount(amount: float) -> None:
        """
        Validate money amount.
        
        Raises:
            ValidationError: If amount is invalid
        """
        if amount < 0:
            raise ValidationError("Money amount cannot be negative", field="money")
        
        if amount > 1_000_000_000:  # 1 billion limit
            raise ValidationError("Money amount exceeds maximum limit", field="money")
    
    @staticmethod
    def validate_can_purchase(player: PlayerState, cost: float) -> None:
        """
        Validate if player can afford a purchase.
        
        Raises:
            ValidationError: If player cannot afford
        """
        if player.money < cost:
            raise ValidationError(
                f"Insufficient funds. Required: ₹{cost:.2f}, Available: ₹{player.money:.2f}",
                field="money"
            )
    
    @staticmethod
    def validate_land_position(player: PlayerState, position: Position) -> None:
        """
        Validate land position for purchase.
        
        Raises:
            ValidationError: If position is invalid
        """
        # Check if already owned
        if player.has_land_at(position):
            raise ValidationError(
                f"Land at position ({position.x}, {position.y}) is already owned",
                field="position"
            )
        
        # Check if adjacent to owned land (must be expanding from existing land)
        if len(player.land_tiles) > 0:
            is_adjacent = False
            for tile in player.land_tiles:
                if abs(tile.position.x - position.x) + abs(tile.position.y - position.y) == 1:
                    is_adjacent = True
                    break
            
            if not is_adjacent:
                raise ValidationError(
                    "New land must be adjacent to existing land",
                    field="position"
                )
