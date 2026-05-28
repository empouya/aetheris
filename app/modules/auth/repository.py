from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import RefreshSession, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        normalized_email = email.lower().strip()
        result = await self.session.execute(select(User).where(User.email == normalized_email))
        return result.scalar_one_or_none()

    async def add(self, user: User) -> User:
        self.session.add(user)
        await self.session.flush()
        return user

    async def add_refresh_session(self, refresh_session: RefreshSession) -> RefreshSession:
        self.session.add(refresh_session)
        await self.session.flush()
        return refresh_session

    async def get_active_refresh_session_by_hash(
        self,
        token_hash: str,
    ) -> RefreshSession | None:
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(RefreshSession).where(
                RefreshSession.token_hash == token_hash,
                RefreshSession.revoked_at.is_(None),
                RefreshSession.expires_at > now,
            )
        )
        return result.scalar_one_or_none()
