from datetime import UTC, datetime

from app.core.security import hash_password, verify_password
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate


class AuthenticationFailedError(Exception):
    pass


class UserAlreadyExistsError(Exception):
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
