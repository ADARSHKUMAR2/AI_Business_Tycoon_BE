from typing import List
from services.game.models.employee import Employee, EmployeeCreate
from services.game.models.business import Business
from services.game.models.player import PlayerState
from services.game.utils.state_manager import state_manager
from services.game.generators.employee_generator import EmployeeGenerator
from services.game.validators.business_validator import BusinessValidator
from services.game.controllers.business_controller import BusinessController
from shared.exceptions import NotFoundError

class EmployeeController:
    """Controller for employee management."""

    @staticmethod
    def get_candidates(count: int = 3) -> List[Employee]:
        """Generate random candidates for hire."""
        return EmployeeGenerator.generate_multiple_employees(count)

    @staticmethod
    async def hire_employee(player_id: str, business_id: str, data: EmployeeCreate) -> Employee:
        """Hire a new employee for a business."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)
        
        # Validation
        BusinessValidator.validate_can_hire_employee(business)
        
        # Generate full employee from basic data
        employee = EmployeeGenerator.generate_employee(
            role=data.role,
            name=data.name,
            business_id=business_id
        )
        
        # Add to business
        business.employees.append(employee)
        business.update_timestamp()
        
        # Update player stats
        player.stats.employees_hired += 1
        
        # Save
        player.businesses[idx] = business
        await state_manager.save_player(player)
        
        return employee

    @staticmethod
    async def get_employees(player_id: str, business_id: str) -> List[Employee]:
        """List all employees in a business."""
        player = await state_manager.load_player(player_id)
        _, business = await BusinessController._find_business_in_player(player, business_id)
        return business.employees

    @staticmethod
    async def fire_employee(player_id: str, business_id: str, employee_id: str) -> dict:
        """Fire an employee."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)
        
        # Find employee
        emp_idx = -1
        for i, emp in enumerate(business.employees):
            if emp.employee_id == employee_id:
                emp_idx = i
                break
                
        if emp_idx == -1:
            raise NotFoundError("Employee", employee_id)
            
        # Remove employee
        business.employees.pop(emp_idx)
        business.update_timestamp()
        
        # Save
        player.businesses[idx] = business
        await state_manager.save_player(player)
        
        return {"message": f"Employee {employee_id} fired successfully"}
