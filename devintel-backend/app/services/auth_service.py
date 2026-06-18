from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.core.exceptions import AuthenticationError, ConflictError
from app.schemas.auth import SignupRequest, LoginRequest
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def signup(self, data: SignupRequest) -> tuple[User, str, str]:
        """
        Creates a new user. Returns (user, access_token, refresh_token).
        Raises ConflictError if email already registered.
        """
        if await self.user_repo.email_exists(data.email):
            raise ConflictError(f"Email '{data.email}' is already registered")

        hashed = hash_password(data.password)
        user = await self.user_repo.create_email_user(
            email=data.email,
            hashed_password=hashed,
            full_name=data.full_name,
        )

        logger.info("New user registered: id=%s email=%s", user.id, user.email)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    async def login(self, data: LoginRequest) -> tuple[User, str, str]:
        """
        Authenticates email/password. Returns (user, access_token, refresh_token).
        Raises AuthenticationError on failure.
        """
        user = await self.user_repo.get_by_email(data.email)

        password_ok = verify_password(
            data.password,
            user.hashed_password if user and user.hashed_password else "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        )

        if not user or not password_ok:
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        logger.info("User logged in: id=%s", user.id)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """
        Validates a refresh token and issues new access + refresh tokens.
        Returns (new_access_token, new_refresh_token).
        """
        from app.core.security import decode_refresh_token

        user_id = decode_refresh_token(refresh_token)
        if user_id is None:
            raise AuthenticationError("Invalid or expired refresh token")

        user = await self.user_repo.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)
        return new_access, new_refresh
