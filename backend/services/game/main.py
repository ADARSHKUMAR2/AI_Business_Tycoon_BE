import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from shared.exceptions import (
    BusinessTycoonException,
    log_business_exception,
    log_request_validation_error,
)

logger = logging.getLogger("game-service")


from services.game.routes import (
    player_routes,
    business_routes,
    employee_routes,
    land_routes,
    delivery_routes,
    world_state_routes,
    leaderboard_routes,
    realtime_routes,
    event_routes,
)
from shared.database import init_db
import os


async def game_exception_handler(request: Request, exc: BusinessTycoonException):
    log_business_exception(logger, request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"message": exc.message, "details": exc.details}},
    )


async def game_validation_exception_handler(request: Request, exc: RequestValidationError):
    await log_request_validation_error(logger, request, exc)
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"message": "Request validation failed", "details": exc.errors()}},
    )

app = FastAPI(
    title="Game Service",
    description="AI Business Tycoon Game Logic Service",
    version="0.1.0",
)

# Exception handlers for Game Service
app.add_exception_handler(BusinessTycoonException, game_exception_handler)
app.add_exception_handler(RequestValidationError, game_validation_exception_handler)

# Include Game Routers
app.include_router(player_routes.router)
app.include_router(business_routes.router)
app.include_router(employee_routes.router)
app.include_router(land_routes.router)
app.include_router(delivery_routes.router)
app.include_router(world_state_routes.router)
app.include_router(leaderboard_routes.router)
app.include_router(realtime_routes.router)
app.include_router(event_routes.router)

@app.on_event("startup")
async def startup_event():
    os.makedirs("./data", exist_ok=True)
    await init_db()
    print("Game Service Started on Port 8002!")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "game-service"}
