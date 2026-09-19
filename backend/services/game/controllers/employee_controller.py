from typing import List

from services.game.models.employee import Employee, EmployeeCreate, EmployeeUpgradeRequest
from services.game.models.business import Business
from services.game.models.player import PlayerState
from services.game.utils.state_manager import state_manager
from services.game.generators.employee_generator import EmployeeGenerator
from services.game.validators.business_validator import BusinessValidator
from services.game.validators.player_validator import PlayerValidator
from services.game.controllers.business_controller import BusinessController
from services.game.config.constants import (
    UPGRADE_COST_BASE,
    UPGRADE_STAT_INCREMENT,
    UPGRADE_CARRY_CAP_INCREMENT,
    UPGRADE_SPEED_MAX,
    UPGRADE_CARRY_MAX,
)
from services.game.config.settings import game_settings
from shared.exceptions import NotFoundError, InvalidOperationError


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

        # ── Deduct money safely on the backend! ──
        if data.role == "restocker":
            cost = game_settings.restocker_hire_cost
        elif data.role == "cleaner":
            cost = game_settings.cleaner_hire_cost
        else:
            cost = game_settings.cashier_hire_cost
            
        PlayerValidator.validate_can_purchase(player, cost)
        player.deduct_money(cost)
        player.stats.total_expenses += cost
        # ────────────────────────────────────────────────

        # Generate full employee from role + name
        employee = EmployeeGenerator.generate_employee(
            role=data.role,
            name=data.name,
            business_id=business_id,
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
        """Fire (remove) an employee from a business."""
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        # Find employee index
        emp_idx = next(
            (i for i, emp in enumerate(business.employees) if emp.employee_id == employee_id),
            -1,
        )
        if emp_idx == -1:
            raise NotFoundError("Employee", employee_id)

        business.employees.pop(emp_idx)
        business.update_timestamp()

        player.businesses[idx] = business
        await state_manager.save_player(player)

        return {"message": f"Employee {employee_id} fired successfully"}

    @staticmethod
    async def upgrade_employee(
        player_id:   str,
        business_id: str,
        employee_id: str,
        request:     EmployeeUpgradeRequest,
    ) -> Employee:
        """
        Upgrade a single stat ('speed' or 'carry_capacity') for an employee.

        Cost formula:
          - speed:          UPGRADE_COST_BASE * current_speed  * UPGRADE_STAT_INCREMENT
          - carry_capacity: UPGRADE_COST_BASE * current_carry  * UPGRADE_CARRY_CAP_INCREMENT

        Example: speed = 70 → cost = 10 * 70 * 5 = ₹3,500
        """
        player = await state_manager.load_player(player_id)
        idx, business = await BusinessController._find_business_in_player(player, business_id)

        # Find the employee
        emp_idx = next(
            (i for i, emp in enumerate(business.employees) if emp.employee_id == employee_id),
            -1,
        )
        if emp_idx == -1:
            raise NotFoundError("Employee", employee_id)

        employee = business.employees[emp_idx]

        # ── Speed upgrade ──────────────────────────────────────────────
        if request.stat == "speed":
            current = employee.stats.speed
            if current >= UPGRADE_SPEED_MAX:
                raise InvalidOperationError(
                    f"Employee speed is already at maximum ({UPGRADE_SPEED_MAX})."
                )
            cost = UPGRADE_COST_BASE * current * UPGRADE_STAT_INCREMENT
            PlayerValidator.validate_can_purchase(player, cost)

            player.deduct_money(cost)
            player.stats.total_expenses += cost
            employee.stats.speed = min(UPGRADE_SPEED_MAX, current + UPGRADE_STAT_INCREMENT)

        # ── Carry capacity upgrade ─────────────────────────────────────
        elif request.stat == "carry_capacity":
            current = employee.stats.carry_capacity
            if current >= UPGRADE_CARRY_MAX:
                raise InvalidOperationError(
                    f"Employee carry capacity is already at maximum ({UPGRADE_CARRY_MAX})."
                )
            cost = UPGRADE_COST_BASE * current * UPGRADE_CARRY_CAP_INCREMENT
            PlayerValidator.validate_can_purchase(player, cost)

            player.deduct_money(cost)
            player.stats.total_expenses += cost
            employee.stats.carry_capacity = min(
                UPGRADE_CARRY_MAX, current + UPGRADE_CARRY_CAP_INCREMENT
            )

        # Write back and save
        business.employees[emp_idx] = employee
        business.update_timestamp()
        player.businesses[idx] = business
        await state_manager.save_player(player)

        return employee
