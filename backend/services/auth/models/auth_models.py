from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(...)
    password: str = Field(..., min_length=6)

class LoginRequest(BaseModel):
    email: str = Field(...)
    password: str = Field(...)

class GuestLoginRequest(BaseModel):
    name: Optional[str] = Field(None, description="Optional name for the guest")

class AuthResponse(BaseModel):
    player_id: str
    name: str
    email: Optional[str] = None
    is_guest: bool
