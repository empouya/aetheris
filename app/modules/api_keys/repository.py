from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.api_keys.models import ApiKey


class ApiKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, api_key: ApiKey) -> ApiKey:
        self.session.add(api_key)
        await self.session.flush()
        return api_key

    async def list_for_organization(self, organization_id: UUID) -> list[ApiKey]:
        result = await self.session.execute(
            select(ApiKey)
            .where(ApiKey.organization_id == organization_id)
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_for_organization(
        self,
        *,
        api_key_id: UUID,
        organization_id: UUID,
    ) -> ApiKey | None:
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.id == api_key_id,
                ApiKey.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_prefix(self, key_prefix: str) -> list[ApiKey]:
        result = await self.session.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == key_prefix,
                ApiKey.revoked_at.is_(None),
            )
        )
        return list(result.scalars().all())
