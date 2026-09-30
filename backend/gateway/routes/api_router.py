from fastapi import APIRouter
from services.game.routes import player_routes, business_routes, employee_routes, land_routes, world_state_routes, event_routes
from gateway.controllers import health_controller

# Main API router v1
api_v1_router = APIRouter(prefix="/api")

# Include all service routers
api_v1_router.include_router(player_routes.router)
api_v1_router.include_router(business_routes.router)
api_v1_router.include_router(employee_routes.router)
api_v1_router.include_router(land_routes.router)
api_v1_router.include_router(world_state_routes.router)
api_v1_router.include_router(event_routes.router)

# Root router for health checks etc
root_router = APIRouter()
root_router.include_router(health_controller.router)
