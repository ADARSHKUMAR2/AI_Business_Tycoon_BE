from typing import List

from services.game.models.business import Business, BusinessCreate, BusinessType, TransactionBatchSync
from services.game.models.player import PlayerState
from services.game.models.inventory import InventoryItem, InventoryUpdate, PriceUpdate, ShelfUpgradeRequest
from services.game.models.land import LandType, Position
from services.game.models.trash import TrashItem, SpawnTrashRequest
from services.game.config.settings import game_settings
from services.game.config.constants import SHELF_UPGRADE_COSTS, SHELF_MAX_CAPACITY
from services.game.utils.state_manager import state_manager
from services.game.validators.business_validator import BusinessValidator
from services.game.validators.player_validator import PlayerValidator
from shared.exceptions import NotFoundError, InvalidOperationError

class BusinessController:
    """Controller for business-related logic."""

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def _find_business_in_player(player: PlayerState, business_id: str) -> tuple[int, Business]:
        """Helper: find a business by ID and return (index, business)."""
        for idx, biz in enumerate(player.businesses):
            if biz.business_id == business_id:
                return idx, biz
        raise NotFoundError("Business", business_id)

    # ──────────────────────────────────────────────────────────────────
    # Business CRUD
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def create_business(data: BusinessCreate) -> Business:
        """Create a new business for a player."""
        BusinessValidator.validate_business_name(data.name)

        player = await state_manager.load_player(data.player_id)
        pos    = Position(x=data.position_x, y=data.position_y)

        BusinessValidator.validate_business_position(player, pos)

        # Determine build cost and inventory template
        build_cost       = game_settings.kirana_build_cost
        inventory_source = game_settings.default_inventory_items

        match data.business_type:
            case BusinessType.PIZZA:
                build_cost = game_settings.pizza_build_cost
                inventory_source = game_settings.pizza_inventory_items
            case BusinessType.CAFE:
                build_cost = game_settings.cafe_build_cost
                inventory_source = game_settings.cafe_inventory_items
            case BusinessType.RESTAURANT:
                build_cost = game_settings.restaurant_build_cost
                inventory_source = game_settings.restaurant_inventory_items
            case _:
                build_cost = game_settings.kirana_build_cost
                inventory_source = game_settings.default_inventory_items

        PlayerValidator.validate_can_purchase(player, build_cost)

        player.deduct_money(build_cost)
        player.stats.total_expenses += build_cost

        # Convert dict template → InventoryItem objects
        inventory_items = {
            key: InventoryItem(**item_data)
            for key, item_data in inventory_source.items()
        }

        business = Business(
            player_id=player.player_id,
            business_type=data.business_type,
            name=data.name,
            position_x=data.position_x,
            position_y=data.position_y,
            inventory=inventory_items,
        )

        # Mark the land tile as a SHOP
        for tile in player.land_tiles:
            if tile.position == pos:
                tile.tile_type  = LandType.SHOP
                tile.business_id = business.business_id
                break

        player.businesses.append(business)
        player.stats.businesses_owned += 1
        await state_manager.save_player(player)

        return business

    @staticmethod
    async def get_business(player_id: str, business_id: str) -> Business:
        """Get full business details."""
        player = await state_manager.load_player(player_id)
        _, business = await BusinessController._find_business_in_player(player, business_id)
        return business

    @staticmethod
    async def update_inventory(player_id: str, business_id: str, update: InventoryUpdate) -> Business:
        """Update inventory stock or price for one item."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        BusinessValidator.validate_inventory_update(business, update.item_key)

        item = business.inventory[update.item_key]

        # Validate stock doesn't exceed shelf capacity
        if update.stock > item.max_stock:
            raise InvalidOperationError(
                f"Cannot stock {update.stock} units — shelf capacity is {item.max_stock}. "
                f"Upgrade the shelf first."
            )

        # Charge the player if restocking
        if update.stock > item.stock:
            added_stock = update.stock - item.stock
            cost        = added_stock * item.cost
            PlayerValidator.validate_can_purchase(player, cost)
            player.deduct_money(cost)
            player.stats.total_expenses  += cost
            business.stats.total_expenses += cost

        item.stock = update.stock
        item.price = update.price

        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    @staticmethod
    async def set_price_multiplier(player_id: str, business_id: str, update: PriceUpdate) -> Business:
        """Update the global price multiplier for a business."""
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

    # ──────────────────────────────────────────────────────────────────
    # Phase 3: Trash / Cleanliness
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def get_trash(player_id: str, business_id: str) -> List[TrashItem]:
        """
        Return the full list of active trash items for a business.
        Called by Godot on game load so the Cleaner AI can see what needs cleaning.
        """
        player = await state_manager.load_player(player_id)
        _, business = await BusinessController._find_business_in_player(player, business_id)
        return business.trash_items

    @staticmethod
    async def spawn_trash(
        player_id:   str,
        business_id: str,
        request:     SpawnTrashRequest,
    ) -> Business:
        """
        Record a new piece of trash dropped by a customer.
        Recalculates store_rating after adding.
        Called by the Godot client whenever a customer drops trash.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        trash = TrashItem(position_x=request.position_x, position_y=request.position_y)
        business.trash_items.append(trash)
        business.recalculate_rating()
        business.update_timestamp()

        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    @staticmethod
    async def remove_trash(
        player_id:   str,
        business_id: str,
        trash_id:    str,
    ) -> Business:
        """
        Remove a piece of trash that the Cleaner AI has picked up.
        Recalculates store_rating after removal.
        Called by the Godot client when the Cleaner reaches and cleans a TrashItem.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        trash_idx = next(
            (i for i, t in enumerate(business.trash_items) if t.trash_id == trash_id),
            -1,
        )
        if trash_idx == -1:
            raise NotFoundError("TrashItem", trash_id)

        business.trash_items.pop(trash_idx)
        business.recalculate_rating()
        business.update_timestamp()

        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    # ──────────────────────────────────────────────────────────────────
    # Phase 3: Shelf Upgrades
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def upgrade_shelf(
        player_id:   str,
        business_id: str,
        request:     ShelfUpgradeRequest,
    ) -> Business:
        """
        Upgrade the max_stock capacity of one shelf/inventory item.

        Rules:
        - target_capacity must be 20 or 30 (enforced by the model's Literal type).
        - Cannot downgrade (target must be larger than current max_stock).
        - Cost comes from SHELF_UPGRADE_COSTS lookup table.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        BusinessValidator.validate_inventory_update(business, request.item_key)

        item = business.inventory[request.item_key]

        # Guard: must be an upgrade, not a downgrade or no-op
        if request.target_capacity <= item.max_stock:
            raise InvalidOperationError(
                f"Shelf for '{request.item_key}' already has capacity {item.max_stock}. "
                f"Target capacity must be greater than current capacity."
            )

        cost = SHELF_UPGRADE_COSTS.get(request.target_capacity)
        if cost is None:
            raise InvalidOperationError(
                f"Invalid target capacity: {request.target_capacity}. "
                f"Valid options are: {list(SHELF_UPGRADE_COSTS.keys())}"
            )

        PlayerValidator.validate_can_purchase(player, cost)

        player.deduct_money(cost)
        player.stats.total_expenses  += cost
        business.stats.total_expenses += cost

        item.max_stock = request.target_capacity

        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business

    # ──────────────────────────────────────────────────────────────────
    # Batched Transactions Sync
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    async def sync_business_transactions(
        player_id:   str,
        business_id: str,
        request:     TransactionBatchSync 
    ) -> Business:
        """
        Processes a batched sync of sales from the local client.
        Deducts sold items from inventory and adds revenue.
        """
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        # 1. Process items sold
        for item_key, quantity in request.items_sold.items():
            if item_key in business.inventory:
                item = business.inventory[item_key]
                # Safely deduct stock, protecting against negatives
                item.stock = max(0, item.stock - quantity)
                item.total_sold += quantity

        # 2. Add revenue to business stats
        business.stats.total_revenue += request.total_revenue
        business.stats.total_customers_served += request.total_customers_served
        
        # Recalculate average transaction
        if business.stats.total_customers_served > 0:
            business.stats.average_transaction = (
                business.stats.total_revenue / business.stats.total_customers_served
            )

        # 3. Add money to the player's wallet
        # Assuming player.money exists. Using += since player.deduct_money is for subtractions
        player.money += request.total_revenue

        # 4. Save state
        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return business
