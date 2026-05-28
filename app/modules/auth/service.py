from datetime import UTC, datetime

from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import UserCreate


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
