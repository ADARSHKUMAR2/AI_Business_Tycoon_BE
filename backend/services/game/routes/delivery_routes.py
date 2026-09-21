"""
Delivery routes for Phase 4 Feature 3.
"""

from fastapi import APIRouter, Path

from services.game.controllers.delivery_controller import DeliveryController
from services.game.models.business import Business
from services.game.models.delivery import DeliveryStatusResponse

router = APIRouter(prefix="/delivery", tags=["Delivery"])


@router.get(
    "/{player_id}/{business_id}/status",
    response_model=DeliveryStatusResponse,
    summary="Get supply delivery status for a business"
)
async def get_delivery_status(
    player_id: str = Path(..., description="Player ID"),
    business_id: str = Path(..., description="Business ID"),
):
    return await DeliveryController.get_delivery_status(player_id, business_id)


@router.post(
    "/{player_id}/{business_id}/restock",
    response_model=Business,
    summary="Force a manual restock (testing/admin)"
)
async def trigger_manual_restock(
    player_id: str = Path(..., description="Player ID"),
    business_id: str = Path(..., description="Business ID"),
):
    return await DeliveryController.trigger_manual_restock(player_id, business_id)


@router.post(
    "/{player_id}/{business_id}/express",
    response_model=Business,
    summary="Pay to trigger immediate supply delivery"
)
async def request_express_delivery(
    player_id: str = Path(..., description="Player ID"),
    business_id: str = Path(..., description="Business ID"),
):
    return await DeliveryController.request_express_delivery(player_id, business_id)
