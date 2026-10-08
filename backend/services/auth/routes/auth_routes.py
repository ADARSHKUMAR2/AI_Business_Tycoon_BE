from fastapi import APIRouter
from services.auth.models.auth_models import RegisterRequest, LoginRequest, GuestLoginRequest, AuthResponse
from services.auth.controllers.auth_controller import AuthController

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    return await AuthController.register(request)

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    return await AuthController.login(request)

@router.post("/guest", response_model=AuthResponse)
async def login_guest(request: GuestLoginRequest):
    name = request.name if request.name else "Guest Tycoon"
    return await AuthController.login_guest(name)