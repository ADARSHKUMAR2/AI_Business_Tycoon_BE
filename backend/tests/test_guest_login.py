from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth.controllers.auth_controller import AuthController
from shared.exceptions import ValidationError


@pytest.mark.asyncio
async def test_guest_login_uses_valid_default_name():
    player = MagicMock(player_id="player_test")
    player.name = "Guest Tycoon"
    player.email = None
    with patch(
        "services.auth.controllers.auth_controller.state_manager.save_player",
        new_callable=AsyncMock,
    ) as save_player, patch(
        "services.auth.controllers.auth_controller.PlayerState",
        return_value=player,
    ):
        response = await AuthController.login_guest()

    assert response.name == "Guest Tycoon"
    assert response.is_guest is True
    save_player.assert_awaited_once()
    assert save_player.await_args.args[0].name == "Guest Tycoon"


@pytest.mark.asyncio
async def test_guest_login_accepts_valid_custom_name():
    player = MagicMock(player_id="player_test")
    player.name = "Adarsh Kumar 7"
    player.email = None
    with patch(
        "services.auth.controllers.auth_controller.state_manager.save_player",
        new_callable=AsyncMock,
    ), patch(
        "services.auth.controllers.auth_controller.PlayerState",
        return_value=player,
    ):
        response = await AuthController.login_guest("Adarsh Kumar 7")

    assert response.name == "Adarsh Kumar 7"


@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["Guest_Tycoon", "Guest-Tycoon", "Guest Tycoon!"])
async def test_guest_login_rejects_names_not_supported_by_player_updates(name: str):
    with patch(
        "services.auth.controllers.auth_controller.state_manager.save_player",
        new_callable=AsyncMock,
    ) as save_player:
        with pytest.raises(ValidationError) as error:
            await AuthController.login_guest(name)

    assert error.value.status_code == 422
    assert error.value.details == {"field": "name"}
    save_player.assert_not_awaited()