from fastapi import APIRouter, Path, Query
from typing import List

from services.game.models.employee import Employee, EmployeeCreate
from services.game.controllers.employee_controller import EmployeeController

router = APIRouter(prefix="/employee", tags=["Employee"])

@router.get("/candidates", response_model=List[Employee])
async def get_candidates(count: int = Query(3, ge=1, le=10)):
    """Get random candidates for hire."""
    return EmployeeController.get_candidates(count)

@router.get("/{player_id}/{business_id}", response_model=List[Employee])
async def get_employees(
    player_id: str = Path(...),
    business_id: str = Path(...)
):
    """List all employees in a business."""
    return EmployeeController.get_employees(player_id, business_id)

@router.post("/{player_id}/{business_id}/hire", response_model=Employee)
async def hire_employee(
    data: EmployeeCreate,
    player_id: str = Path(...),
    business_id: str = Path(...)
):
    """Hire a new employee."""
    return EmployeeController.hire_employee(player_id, business_id, data)

@router.delete("/{player_id}/{business_id}/{employee_id}")
async def fire_employee(
    player_id: str = Path(...),
    business_id: str = Path(...),
    employee_id: str = Path(...)
):
    """Fire an employee."""
    return EmployeeController.fire_employee(player_id, business_id, employee_id)
