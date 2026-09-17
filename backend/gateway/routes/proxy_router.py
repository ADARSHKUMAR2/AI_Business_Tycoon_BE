import httpx
from fastapi import APIRouter, Request, HTTPException, Response
import os

router = APIRouter()

# Service URLs from environment or defaults
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://localhost:8001")
GAME_SERVICE_URL = os.getenv("GAME_SERVICE_URL", "http://localhost:8002")

# We use an httpx AsyncClient for efficient proxying
# It's best practice to share one client instance
client = httpx.AsyncClient()

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
        # Make the proxied request
        proxy_req = client.build_request(
            method=request.method,
            url=url,
            params=params,
            headers=headers,
            content=body
        )
        
        proxy_res = await client.send(proxy_req)
        
        # Return the response exactly as the microservice sent it
        return Response(
            content=proxy_res.content,
            status_code=proxy_res.status_code,
            headers=dict(proxy_res.headers)
        )
        
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Service unavailable: Failed to connect to backend service. ({str(e)})"
        )

# ==========================================
# Proxy Routes
# ==========================================

@router.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_auth(request: Request, path: str):
    """Proxy all /auth/ requests to the Auth Service (Port 8001)"""
    return await forward_request(request, AUTH_SERVICE_URL, path)

@router.api_route("/game/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_game(request: Request, path: str):
    """Proxy all /game/ requests to the Game Service (Port 8002)"""
    return await forward_request(request, GAME_SERVICE_URL, path)
