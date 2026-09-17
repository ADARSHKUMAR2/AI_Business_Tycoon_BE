"""
Employee models for business staff management.
"""
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional
import uuid


class EmployeeRole(str, Enum):
    """Employee roles available in Phase 1."""
    CASHIER = "cashier"
    # Future: MANAGER = "manager", COOK = "cook", etc.


class EmployeeStats(BaseModel):
    """Employee performance statistics."""
    speed: int = Field(..., ge=1, le=100, description="Service speed (1-100)")
    accuracy: int = Field(..., ge=1, le=100, description="Accuracy (1-100)")
    customer_care: int = Field(..., ge=1, le=100, description="Customer care skill (1-100)")
    
    def calculate_performance_score(self) -> float:
        """Calculate overall performance score."""
        return (self.speed + self.accuracy + self.customer_care) / 3.0


class EmployeeCreate(BaseModel):
    """Schema for creating/hiring a new employee."""
    name: str = Field(..., min_length=2, max_length=50, description="Employee name")
    role: EmployeeRole = EmployeeRole.CASHIER
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Ravi Kumar",
                "role": "cashier"
            }
        }
    }


class Employee(BaseModel):
    """Employee model with stats and progression."""
    employee_id: str = Field(default_factory=lambda: f"emp_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=2, max_length=50)
    role: EmployeeRole
    stats: EmployeeStats
    salary_per_day: float = Field(..., gt=0, description="Daily salary in ₹")
    experience: int = Field(0, ge=0, description="Experience points")
    level: int = Field(1, ge=1, le=10, description="Employee level")
    hired_at: datetime = Field(default_factory=datetime.utcnow)
    business_id: Optional[str] = Field(None, description="Assigned business ID")
    
    def get_monthly_salary(self) -> float:
        """Calculate monthly salary (30 days)."""
        return self.salary_per_day * 30
    
    def add_experience(self, points: int):
        """Add experience points and check for level up."""
        self.experience += points
        # Level up every 100 XP
        new_level = min(10, (self.experience // 100) + 1)
        if new_level > self.level:
            self.level = new_level
            # Boost stats on level up
            self.stats.speed = min(100, self.stats.speed + 5)
            self.stats.accuracy = min(100, self.stats.accuracy + 5)
            self.stats.customer_care = min(100, self.stats.customer_care + 5)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "employee_id": "emp_a1b2c3d4",
                "name": "Ravi Kumar",
                "role": "cashier",
                "stats": {
                    "speed": 72,
                    "accuracy": 91,
                    "customer_care": 64
                },
                "salary_per_day": 1200.0,
                "experience": 0,
                "level": 1,
                "hired_at": "2026-09-17T08:00:00Z",
                "business_id": "biz_xyz123"
            }
        }
    }
