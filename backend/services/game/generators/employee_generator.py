"""
Employee generator for creating NPCs with random stats.
"""
import random
from typing import Optional

from services.game.models.employee import Employee, EmployeeRole, EmployeeStats
from services.game.config.constants import (
    INDIAN_FIRST_NAMES,
    INDIAN_LAST_NAMES,
    EMPLOYEE_STAT_MIN,
    EMPLOYEE_STAT_MAX,
)
from services.game.config.settings import game_settings


class EmployeeGenerator:
    """Generates employees with randomized stats."""
    
    @staticmethod
    def generate_random_name() -> str:
        """Generate a random Indian name."""
        first_name = random.choice(INDIAN_FIRST_NAMES)
        last_name = random.choice(INDIAN_LAST_NAMES)
        return f"{first_name} {last_name}"
    
    @staticmethod
    def generate_random_stats() -> EmployeeStats:
        """Generate random employee stats."""
        # Generate stats with normal distribution around 60
        speed = max(EMPLOYEE_STAT_MIN, min(EMPLOYEE_STAT_MAX, int(random.gauss(60, 15))))
        accuracy = max(EMPLOYEE_STAT_MIN, min(EMPLOYEE_STAT_MAX, int(random.gauss(60, 15))))
        customer_care = max(EMPLOYEE_STAT_MIN, min(EMPLOYEE_STAT_MAX, int(random.gauss(60, 15))))
        
        return EmployeeStats(
            speed=speed,
            accuracy=accuracy,
            customer_care=customer_care
        )
    
    @staticmethod
    def calculate_salary_from_stats(stats: EmployeeStats) -> float:
        """Calculate salary based on employee stats."""
        # Performance score 0-100
        performance = stats.calculate_performance_score()
        
        # Salary ranges from min to max based on performance
        salary_range = game_settings.default_cashier_salary_max - game_settings.default_cashier_salary_min
        salary = game_settings.default_cashier_salary_min + (salary_range * (performance / 100))
        
        # Round to nearest 50
        return round(salary / 50) * 50
    
    @classmethod
    def generate_employee(
        cls,
        role: EmployeeRole = EmployeeRole.CASHIER,
        name: Optional[str] = None,
        business_id: Optional[str] = None
    ) -> Employee:
        """
        Generate a complete employee with random stats.
        
        Args:
            role: Employee role
            name: Optional custom name (random if not provided)
            business_id: Optional business assignment
            
        Returns:
            Employee instance
        """
        if name is None:
            name = cls.generate_random_name()
        
        stats = cls.generate_random_stats()
        salary = cls.calculate_salary_from_stats(stats)
        
        return Employee(
            name=name,
            role=role,
            stats=stats,
            salary_per_day=salary,
            business_id=business_id
        )
    
    @classmethod
    def generate_multiple_employees(cls, count: int, role: EmployeeRole = EmployeeRole.CASHIER) -> list[Employee]:
        """Generate multiple employees."""
        return [cls.generate_employee(role=role) for _ in range(count)]
