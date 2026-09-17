import sys
import uvicorn
import subprocess

def start_all():
    """Start all services using honcho and Procfile."""
    subprocess.run(["honcho", "start"])

def start_gateway():
    """Start only the API Gateway on port 8000."""
    uvicorn.run("gateway.main:app", host="0.0.0.0", port=8000, reload=True)

def start_auth():
    """Start only the Auth Service on port 8001."""
    uvicorn.run("services.auth.main:app", host="0.0.0.0", port=8001, reload=True)

def start_game():
    """Start only the Game Service on port 8002."""
    uvicorn.run("services.game.main:app", host="0.0.0.0", port=8002, reload=True)
