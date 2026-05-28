from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.models import User
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

    async def get_membership(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> Membership | None:
        result = await self.session.execute(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_members(self, organization_id: UUID) -> list[dict[str, object]]:
        result = await self.session.execute(
            select(
                Membership.id.label("id"),
                Membership.organization_id.label("organization_id"),
                Membership.user_id.label("user_id"),
                User.email.label("email"),
                Membership.role.label("role"),
                Membership.created_at.label("created_at"),
            )
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == organization_id)
            .order_by(Membership.created_at.asc())
        )

        return [dict(row) for row in result.mappings().all()]
