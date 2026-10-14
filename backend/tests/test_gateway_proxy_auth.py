from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from gateway.routes import proxy_router


@pytest.mark.asyncio
async def test_forward_request_uses_cloud_run_token_without_overwriting_user_auth(monkeypatch):
    request = AsyncMock()
    request.method = "GET"
    request.query_params = {}
    request.headers = {
        "authorization": "Bearer player-token",
        "host": "gateway.example",
    }

    monkeypatch.setattr(
        proxy_router,
        "_get_upstream_identity_token",
        AsyncMock(return_value="cloud-run-token"),
    )
    monkeypatch.setattr(proxy_router.client, "build_request", lambda **kwargs: kwargs)
    upstream_response = Mock(
        is_error=False,
        content=b'{"ok":true}',
        status_code=200,
        headers={"content-type": "application/json"},
    )
    send = AsyncMock(return_value=upstream_response)
    monkeypatch.setattr(proxy_router.client, "send", send)

    response = await proxy_router.forward_request(request, "https://auth.example", "auth/login")

    sent_headers = send.await_args.args[0]["headers"]
    assert sent_headers["authorization"] == "Bearer player-token"
    assert sent_headers["X-Serverless-Authorization"] == "Bearer cloud-run-token"
    assert "host" not in sent_headers
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_forward_request_does_not_use_identity_token_for_local_http(monkeypatch):
    request = AsyncMock()
    request.method = "GET"
    request.query_params = {}
    request.headers = {"host": "localhost"}
    get_token = AsyncMock(return_value=None)
    monkeypatch.setattr(proxy_router, "_get_upstream_identity_token", get_token)
    monkeypatch.setattr(proxy_router.client, "build_request", lambda **kwargs: kwargs)
    upstream_response = Mock(is_error=False, content=b"ok", status_code=200, headers={})
    send = AsyncMock(return_value=upstream_response)
    monkeypatch.setattr(proxy_router.client, "send", send)

    await proxy_router.forward_request(request, "http://127.0.0.1:8001", "auth/login")

    get_token.assert_awaited_once_with("http://127.0.0.1:8001")
    sent_headers = send.await_args.args[0]["headers"]
    assert "X-Serverless-Authorization" not in sent_headers


@pytest.mark.asyncio
async def test_identity_token_failure_returns_safe_503(monkeypatch):
    request = AsyncMock()
    request.method = "GET"
    request.query_params = {}
    request.headers = {}
    monkeypatch.setattr(
        proxy_router,
        "_get_upstream_identity_token",
        AsyncMock(side_effect=HTTPException(status_code=503, detail="Unable to authenticate with the backend service.")),
    )

    with pytest.raises(HTTPException) as exc_info:
        await proxy_router.forward_request(request, "https://auth.example", "auth/login")

    assert exc_info.value.status_code == 503