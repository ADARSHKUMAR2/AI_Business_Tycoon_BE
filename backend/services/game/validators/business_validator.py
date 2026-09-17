"""
Business data validators.
"""
from services.game.models.business import Business, BusinessCreate
from services.game.models.player import PlayerState
from services.game.models.land import Position
from services.game.config.constants import MAX_EMPLOYEES_PER_BUSINESS, MAX_PRICE_MULTIPLIER, MIN_PRICE_MULTIPLIER
from shared.exceptions import ValidationError, InvalidOperationError


class BusinessValidator:
    """Validates business-related operations."""
    
    @staticmethod
    def validate_business_name(name: str) -> None:
        """Validate business name."""
        if not name or len(name.strip()) < 2:
            raise ValidationError("Business name must be at least 2 characters", field="name")
        
        if len(name) > 100:
            raise ValidationError("Business name must not exceed 100 characters", field="name")
    
    @staticmethod
    def validate_business_position(player: PlayerState, position: Position) -> None:
        """
        Validate business can be built at position.
        
        Raises:
            ValidationError: If position is invalid
        """
        # Check if player owns land at this position
        if not player.has_land_at(position):
            raise ValidationError(
                f"You don't own land at position ({position.x}, {position.y})",
                field="position"
            )
        
        # Check if there's already a business at this position
        existing_business = player.get_business_at(position)
        if existing_business:
            raise ValidationError(
                f"A business already exists at position ({position.x}, {position.y})",
                field="position"
            )
    
    @staticmethod
    def validate_price_multiplier(multiplier: float) -> None:
        """Validate price multiplier."""
        if multiplier < MIN_PRICE_MULTIPLIER:
            raise ValidationError(
                f"Price multiplier cannot be less than {MIN_PRICE_MULTIPLIER}",
                field="price_multiplier"
            )
        
        if multiplier > MAX_PRICE_MULTIPLIER:
            raise ValidationError(
                f"Price multiplier cannot exceed {MAX_PRICE_MULTIPLIER}",
                field="price_multiplier"
            )
    
    @staticmethod
    def validate_can_hire_employee(business: Business) -> None:
        """
        Validate if business can hire more employees.
        
        Raises:
            InvalidOperationError: If cannot hire
        """
        if business.get_employee_count() >= MAX_EMPLOYEES_PER_BUSINESS:
            raise InvalidOperationError(
                f"Business has reached maximum employee limit ({MAX_EMPLOYEES_PER_BUSINESS})"
            )
    
    @staticmethod
    def validate_inventory_update(business: Business, item_key: str) -> None:
        """Validate inventory item exists."""
        if item_key not in business.inventory:
            raise ValidationError(
                f"Item '{item_key}' not found in business inventory",
                field="item_key"
            )
    
    @staticmethod
    def validate_business_is_open(business: Business) -> None:
        """Validate business is open for operations."""
        if not business.is_open:
            raise InvalidOperationError("Business is currently closed")
