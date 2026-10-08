import bcrypt
from shared.exceptions import InvalidOperationError, NotFoundError
from services.game.models.player import PlayerState
from services.game.utils.state_manager import state_manager
from services.auth.models.auth_models import RegisterRequest, LoginRequest, AuthResponse


class AuthController:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

    @staticmethod
    def get_password_hash(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    async def register(request: RegisterRequest) -> AuthResponse:
        # Check if email exists
        existing_player = await PlayerState.find_one(PlayerState.email == request.email)
        if existing_player:
            raise InvalidOperationError("Email already registered")

        hashed_pw = AuthController.get_password_hash(request.password)
        
        # Create player using defaults
        new_player = PlayerState(
            name=request.name,
            email=request.email,
            password_hash=hashed_pw,
            money=15000.0,
            land_tiles=[],
            businesses=[]
        )
        
        await state_manager.save_player(new_player)
        
        return AuthResponse(
            player_id=new_player.player_id,
            name=new_player.name,
            email=new_player.email,
            is_guest=False
        )

    @staticmethod
    async def login(request: LoginRequest) -> AuthResponse:
        player = await PlayerState.find_one(PlayerState.email == request.email)
        if not player or not player.password_hash:
            raise InvalidOperationError("Invalid email or password")
            
        if not AuthController.verify_password(request.password, player.password_hash):
            raise InvalidOperationError("Invalid email or password")
            
        # Update login time
        player.update_login()
        await state_manager.save_player(player)
            
        return AuthResponse(
            player_id=player.player_id,
            name=player.name,
            email=player.email,
            is_guest=False
        )

    @staticmethod
    async def login_guest(name: str = "Guest Tycoon") -> AuthResponse:
        new_player = PlayerState(
            name=name,
            email=None,
            password_hash=None,
            money=15000.0,
            land_tiles=[],
            businesses=[]
        )
        await state_manager.save_player(new_player)
        
        return AuthResponse(
            player_id=new_player.player_id,
            name=new_player.name,
            email=None,
            is_guest=True
        )