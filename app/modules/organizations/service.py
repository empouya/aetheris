from datetime import UTC, datetime
from uuid import UUID

from app.modules.organizations.models import Membership, Organization
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import OrganizationCreate

ORGANIZATION_OWNER_ROLE = "owner"
ADMIN_ROLE = "admin"
MEMBER_ROLE = "member"
VALID_MEMBERSHIP_ROLES = {ORGANIZATION_OWNER_ROLE, ADMIN_ROLE, MEMBER_ROLE}


class OrganizationSlugAlreadyExistsError(Exception):
    pass


class OrganizationAccessDeniedError(Exception):
    pass


class OrganizationService:
    def __init__(self, repository: OrganizationRepository) -> None:
        self.repository = repository

    async def create_organization(
        self,
        *,
        payload: OrganizationCreate,
        owner_user_id: UUID,
    ) -> Organization:
        slug = payload.slug.lower().strip()
        existing_organization = await self.repository.get_by_slug(slug)

        if existing_organization is not None:
            raise OrganizationSlugAlreadyExistsError("Organization slug already exists.")

        now = datetime.now(UTC)

        organization = Organization(
            name=payload.name.strip(),
            slug=slug,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

        await self.repository.add_organization(organization)

        membership = Membership(
            organization_id=organization.id,
            user_id=owner_user_id,
            role=ORGANIZATION_OWNER_ROLE,
            created_at=now,
        )
        await self.repository.add_membership(membership)

        return organization

    async def list_user_organizations(self, user_id: UUID) -> list[Organization]:
        return await self.repository.list_for_user(user_id)

    async def ensure_user_is_member(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> Membership:
        membership = await self.repository.get_membership(
            organization_id=organization_id,
            user_id=user_id,
        )

        if membership is None:
            raise OrganizationAccessDeniedError("User does not belong to this organization.")

        return membership

    async def list_organization_members(
        self,
        *,
        organization_id: UUID,
        requester_user_id: UUID,
    ) -> list[dict[str, object]]:
        await self.ensure_user_is_member(
            organization_id=organization_id,
            user_id=requester_user_id,
        )

        return await self.repository.list_members(organization_id)
