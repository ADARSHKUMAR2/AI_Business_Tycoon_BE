import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from services.game.controllers.delivery_controller import DeliveryController
from services.game.models.business import Business, BusinessType
from services.game.models.delivery import DeliverySchedule
from services.game.models.inventory import InventoryItem
from services.game.models.player import PlayerState


def make_business(schedule: DeliverySchedule) -> Business:
    return Business(
        player_id="player_test",
        business_type=BusinessType.RESTAURANT,
        name="Test Store",
        position_x=0,
        position_y=0,
        delivery_schedule=schedule,
        inventory={
            "ingredient": InventoryItem(
                name="Ingredient",
                cost=1,
                price=2,
                stock=2,
                max_stock=10,
                has_supply_zone=True,
            ),
            "crafted": InventoryItem(
                name="Crafted product",
                cost=1,
                price=2,
                stock=2,
                max_stock=10,
                has_supply_zone=False,
            ),
        },
    )


def test_refresh_does_not_deliver_before_due_time():
    now = datetime(2026, 1, 1, 12, 0)
    schedule = DeliverySchedule(
        delivery_interval_minutes=5,
        last_delivery_at=now - timedelta(minutes=1),
        next_delivery_at=now + timedelta(minutes=4),
    )
    business = make_business(schedule)

    DeliveryController._refresh_delivery_state(business, now)

    assert business.inventory["ingredient"].stock == 2
    assert business.inventory["crafted"].stock == 2
    assert schedule.next_delivery_at == now + timedelta(minutes=4)


def test_due_delivery_only_restocks_supply_items_and_preserves_cadence():
    now = datetime(2026, 1, 1, 12, 16)
    due_at = now - timedelta(minutes=11)
    schedule = DeliverySchedule(
        delivery_interval_minutes=5,
        last_delivery_at=due_at - timedelta(minutes=5),
        next_delivery_at=due_at,
    )
    business = make_business(schedule)

    DeliveryController._refresh_delivery_state(business, now)

    assert business.inventory["ingredient"].stock == 10
    assert business.inventory["crafted"].stock == 2
    assert schedule.last_delivery_at == now - timedelta(minutes=1)
    assert schedule.next_delivery_at == now + timedelta(minutes=4)


def test_inactive_schedule_does_not_restock():
    now = datetime(2026, 1, 1, 12, 0)
    schedule = DeliverySchedule(
        delivery_interval_minutes=5,
        next_delivery_at=now - timedelta(minutes=1),
        is_active=False,
    )
    business = make_business(schedule)

    DeliveryController._refresh_delivery_state(business, now)

    assert business.inventory["ingredient"].stock == 2
    assert business.inventory["crafted"].stock == 2


def make_player(business: Business, money: float = 2000.0):
    return SimpleNamespace(
        player_id="player_test",
        money=money,
        businesses=[business],
    )


def player_document(player, business: Business) -> dict:
    return {
        "player_id": player.player_id,
        "money": player.money,
        "stats": {"total_expenses": 0.0},
        "businesses": [business.model_dump()],
    }


async def run_express_delivery(
    player, business: Business, key: str, result, retry_document: dict | None = None
):
    collection = type("Collection", (), {})()
    documents = [player_document(player, business)]
    if retry_document is not None:
        documents.append(retry_document)
    collection.find_one = AsyncMock(side_effect=documents)
    collection.find_one_and_update = AsyncMock(return_value=result)
    with patch.object(PlayerState, "get_motor_collection", return_value=collection):
        return await DeliveryController.request_express_delivery(
            player.player_id, business.business_id, key
        ), collection


def test_express_delivery_charges_restock_and_records_key_atomically():
    async def scenario():
        business = make_business(DeliverySchedule())
        player = make_player(business)
        updated = make_business(DeliverySchedule())
        updated.business_id = business.business_id
        updated.inventory["ingredient"].stock = 10
        updated.delivery_schedule.processed_express_delivery_keys = ["request-1"]
        updated.delivery_schedule.last_delivery_at = datetime.utcnow()
        updated.delivery_schedule.next_delivery_at = (
            updated.delivery_schedule.last_delivery_at + timedelta(minutes=5)
        )
        returned_business, collection = await run_express_delivery(
            player, business, "request-1", player_document(player, updated)
        )

        assert returned_business.inventory["ingredient"].stock == 10
        assert returned_business.inventory["crafted"].stock == 2
        update = collection.find_one_and_update.await_args.args[1]
        assert update["$inc"] == {"money": -500.0, "stats.total_expenses": 500.0}
        assert update["$push"][
            "businesses.$[biz].delivery_schedule.processed_express_delivery_keys"
        ] == "request-1"
        assert update["$set"][
            "businesses.$[biz].inventory.ingredient.stock"
        ] == 10
        assert "businesses.$[biz].inventory.crafted.stock" not in update["$set"]
        query = collection.find_one_and_update.await_args.args[0]
        assert query["businesses"]["$elemMatch"]["delivery_schedule.processed_express_delivery_keys"] == {
            "$ne": "request-1"
        }

    asyncio.run(scenario())


def test_express_delivery_retry_with_same_key_does_not_write_again():
    async def scenario():
        schedule = DeliverySchedule(processed_express_delivery_keys=["request-1"])
        business = make_business(schedule)
        player = make_player(business)
        returned_business, collection = await run_express_delivery(
            player, business, "request-1", None
        )

        assert returned_business.business_id == business.business_id
        assert returned_business.inventory["ingredient"].stock == 2
        collection.find_one_and_update.assert_not_awaited()

    asyncio.run(scenario())


def test_concurrent_express_delivery_retry_returns_processed_business():
    async def scenario():
        business = make_business(DeliverySchedule())
        player = make_player(business)
        processed = make_business(
            DeliverySchedule(processed_express_delivery_keys=["request-1"])
        )
        processed.business_id = business.business_id
        processed.inventory["ingredient"].stock = 10
        returned_business, collection = await run_express_delivery(
            player,
            business,
            "request-1",
            None,
            retry_document=player_document(player, processed),
        )

        assert returned_business.inventory["ingredient"].stock == 10
        assert "request-1" in returned_business.delivery_schedule.processed_express_delivery_keys
        collection.find_one_and_update.assert_awaited_once()
        assert collection.find_one.await_count == 2

    asyncio.run(scenario())


def test_express_delivery_distinct_key_can_be_processed():
    async def scenario():
        business = make_business(DeliverySchedule(processed_express_delivery_keys=["request-1"]))
        player = make_player(business)
        updated = make_business(DeliverySchedule(processed_express_delivery_keys=["request-1", "request-2"]))
        updated.business_id = business.business_id
        returned_business, collection = await run_express_delivery(
            player, business, "request-2", player_document(player, updated)
        )

        assert "request-2" in returned_business.delivery_schedule.processed_express_delivery_keys
        collection.find_one_and_update.assert_awaited_once()

    asyncio.run(scenario())

