"""
Generators package for creating game entities.
"""
from .employee_generator import EmployeeGenerator
from .customer_generator import CustomerGenerator

__all__ = [
    "EmployeeGenerator",
    "CustomerGenerator",
]
