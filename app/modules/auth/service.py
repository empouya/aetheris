from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import Settings
from app.core.security import generate_secure_token, hash_password, hash_token, verify_password
from app.modules.auth.models import RefreshSession, User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate


class AuthenticationFailedError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UserAccountService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, payload: UserCreate) -> User:
        existing_user = await self.repository.get_by_email(payload.email)
        if existing_user is not None:
            raise UserAlreadyExistsError("A user with this email already exists.")

        now = datetime.now(UTC)

        user = User(
            email=payload.email.lower().strip(),
            password_hash=hash_password(payload.password),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        return await self.repository.add(user)

    async def authenticate_user(self, email: str, password: str) -> User:
        user = await self.repository.get_by_email(email)
        if user is None or not user.is_active:
            raise AuthenticationFailedError("Invalid credentials.")

        if not verify_password(password, user.password_hash):
            raise AuthenticationFailedError("Invalid credentials.")

        return user

    async def create_refresh_token(
        self,
        *,
        settings: Settings,
        user_id: UUID,
    ) -> str:
        now = datetime.now(UTC)
        refresh_token = generate_secure_token()

        refresh_session = RefreshSession(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            revoked_at=None,
            created_at=now,
            rotated_at=None,
        )

        await self.repository.add_refresh_session(refresh_session)
        return refresh_token

    async def rotate_refresh_token(
        self,
        *,
        settings: Settings,
        refresh_token: str,
    ) -> tuple[User, str]:
        now = datetime.now(UTC)
        refresh_session = await self.repository.get_active_refresh_session_by_hash(
            hash_token(refresh_token)
        )

        if refresh_session is None:
            raise InvalidRefreshTokenError("Invalid refresh token.")

        user = await self.repository.get_by_id(refresh_session.user_id)
        if user is None or not user.is_active:
            raise UserNotFoundError("Refresh token user no longer exists.")

        refresh_session.revoked_at = now
        refresh_session.rotated_at = now

        new_refresh_token = await self.create_refresh_token(settings=settings, user_id=user.id)
        return user, new_refresh_token

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        refresh_session = await self.repository.get_active_refresh_session_by_hash(
            hash_token(refresh_token)
        )

        if refresh_session is not None:
            refresh_session.revoked_at = datetime.now(UTC)
