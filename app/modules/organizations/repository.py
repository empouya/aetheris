from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.organizations.models import Membership, Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.session.execute(
            select(Organization).where(
                Organization.slug == slug,
                Organization.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def add_organization(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        return organization

    async def add_membership(self, membership: Membership) -> Membership:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        result = await self.session.execute(
            select(Organization)
            .join(Membership, Membership.organization_id == Organization.id)
            .where(
                Membership.user_id == user_id,
                Organization.deleted_at.is_(None),
            )
            .order_by(Organization.created_at.desc())
        )
        return list(result.scalars().all())
