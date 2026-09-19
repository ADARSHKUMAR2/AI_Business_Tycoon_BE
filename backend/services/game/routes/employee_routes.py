from fastapi import APIRouter, Path, Query
from typing import List

from services.game.models.employee import Employee, EmployeeCreate, EmployeeUpgradeRequest
from services.game.controllers.employee_controller import EmployeeController

router = APIRouter(prefix="/employee", tags=["Employee"])

@router.get("/candidates", response_model=List[Employee])
async def get_candidates(count: int = Query(3, ge=1, le=10)):
    """Get random hire candidates (used by the hiring UI)."""
    return await EmployeeController.get_candidates(count)

@router.get("/{player_id}/{business_id}", response_model=List[Employee])
async def get_employees(
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """List all employees currently hired in a business."""
    return await EmployeeController.get_employees(player_id, business_id)

@router.post("/{player_id}/{business_id}/hire", response_model=Employee)
async def hire_employee(
    data:        EmployeeCreate,
    player_id:   str = Path(...),
    business_id: str = Path(...),
):
    """Hire a new employee for a business."""
    return await EmployeeController.hire_employee(player_id, business_id, data)

@router.put("/{player_id}/{business_id}/{employee_id}/upgrade", response_model=Employee)
async def upgrade_employee(
    request:     EmployeeUpgradeRequest,
    player_id:   str = Path(...),
    business_id: str = Path(...),
    employee_id: str = Path(...),
):
    """
    Upgrade a specific stat for an employee.
    Body: { "stat": "speed" } or { "stat": "carry_capacity" }
    Deducts the upgrade cost from the player's wallet.
    """
    return await EmployeeController.upgrade_employee(
        player_id, business_id, employee_id, request
    )

@router.delete("/{player_id}/{business_id}/{employee_id}")
async def fire_employee(
    player_id:   str = Path(...),
    business_id: str = Path(...),
    employee_id: str = Path(...),
):
    """Fire (permanently remove) an employee from a business."""
    return await EmployeeController.fire_employee(player_id, business_id, employee_id)
