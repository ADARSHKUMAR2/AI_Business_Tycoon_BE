from fastapi import FastAPI
from services.game.routes import player_routes, business_routes, employee_routes, land_routes
from shared.exceptions import BusinessTycoonException
from shared.database import init_db
import os

app = FastAPI(
    title="Game Service",
    description="AI Business Tycoon Game Logic Service",
    version="0.1.0",
)

# Exception handler for Game Service
from fastapi.responses import JSONResponse
from fastapi import Request

async def game_exception_handler(request: Request, exc: BusinessTycoonException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"message": exc.message, "details": exc.details}}
    )

app.add_exception_handler(BusinessTycoonException, game_exception_handler)

# Include Game Routers
app.include_router(player_routes.router)
app.include_router(business_routes.router)
app.include_router(employee_routes.router)
app.include_router(land_routes.router)

@app.on_event("startup")
async def startup_event():
    os.makedirs("./data", exist_ok=True)
    await init_db()
    print("Game Service Started on Port 8002!")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "game-service"}
