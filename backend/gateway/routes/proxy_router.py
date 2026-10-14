import asyncio
import logging
import os
from urllib.parse import urlparse

import google.auth.transport.requests
import google.oauth2.id_token
import httpx
from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger("gateway.proxy")

router = APIRouter()

# Service URLs from environment or defaults
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://127.0.0.1:8001")
GAME_SERVICE_URL = os.getenv("GAME_SERVICE_URL", "http://127.0.0.1:8002")

# We use an httpx AsyncClient for efficient proxying
# It's best practice to share one client instance
client = httpx.AsyncClient()
_google_auth_request = google.auth.transport.requests.Request()


def _get_cloud_run_identity_token(audience: str) -> str:
    """Get a Google-signed ID token for a private Cloud Run service URL."""
    return google.oauth2.id_token.fetch_id_token(_google_auth_request, audience)


async def _get_upstream_identity_token(base_url: str) -> str | None:
    """Get a Cloud Run token for HTTPS services; local HTTP needs no token."""
    if urlparse(base_url).scheme != "https":
        return None

    try:
        return await asyncio.to_thread(_get_cloud_run_identity_token, base_url)
    except Exception as exc:
        logger.exception("Unable to obtain Cloud Run identity token for upstream")
        raise HTTPException(
            status_code=503,
            detail="Unable to authenticate with the backend service.",
        ) from exc

async def forward_request(request: Request, base_url: str, path: str) -> Response:
    """Helper function to forward HTTP requests to backend microservices."""
    url = f"{base_url}/{path}"
    
    # Extract query params
    params = dict(request.query_params)
    
    # Extract body if present
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
        
    # Extract headers (removing host to prevent issues)
    headers = dict(request.headers)
    headers.pop("host", None)
    
    try:
        identity_token = await _get_upstream_identity_token(base_url)
        if identity_token:
            # Cloud Run checks this header for service authentication while
            # preserving the caller's Authorization header for application auth.
            headers["X-Serverless-Authorization"] = f"Bearer {identity_token}"

        # Make the proxied request
        proxy_req = client.build_request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body
        )
        
        proxy_res = await client.send(proxy_req)

        if proxy_res.is_error:
            logger.warning(
                "Upstream API request failed | method=%s url=%s status=%s response_body=%s",
                request.method,
                url,
                proxy_res.status_code,
                proxy_res.text[:10_000],
            )
        
        # Return the response exactly as the microservice sent it
        return Response(
            content=proxy_res.content,
            status_code=proxy_res.status_code,
            headers=dict(proxy_res.headers)
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Service unavailable: Failed to connect to backend service. ({e!s})"
        )

# ==========================================
# Proxy Routes
# ==========================================

@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_auth(request: Request, path: str):
    """Proxy all /auth/ requests to the Auth Service (Port 8001)"""
    return await forward_request(request, AUTH_SERVICE_URL, f"auth/{path}")

@router.api_route("/game/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_game(request: Request, path: str):
    """Proxy all /game/ requests to the Game Service (Port 8002)"""
    return await forward_request(request, GAME_SERVICE_URL, path)
