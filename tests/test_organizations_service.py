from uuid import UUID, uuid4

import pytest
from app.modules.organizations.models import Membership, Organization
from app.modules.organizations.schemas import OrganizationCreate
from app.modules.organizations.service import (
    ORGANIZATION_OWNER_ROLE,
    OrganizationAccessDeniedError,
    OrganizationService,
    OrganizationSlugAlreadyExistsError,
)


class FakeOrganizationRepository:
    def __init__(self) -> None:
        self.organizations_by_slug: dict[str, Organization] = {}
        self.memberships: list[Membership] = []

    async def get_by_slug(self, slug: str) -> Organization | None:
        return self.organizations_by_slug.get(slug)

    async def add_organization(self, organization: Organization) -> Organization:
        self.organizations_by_slug[organization.slug] = organization
        return organization

    async def add_membership(self, membership: Membership) -> Membership:
        self.memberships.append(membership)
        return membership

    async def get_membership(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> Membership | None:
        for membership in self.memberships:
            if membership.organization_id == organization_id and membership.user_id == user_id:
                return membership
        return None

    async def list_for_user(self, user_id: UUID) -> list[Organization]:
        return []

    async def list_members(self, organization_id: UUID) -> list[dict[str, object]]:
        return []


@pytest.mark.asyncio
async def test_create_organization_creates_owner_membership() -> None:
    repository = FakeOrganizationRepository()
    service = OrganizationService(repository)  # type: ignore[arg-type]
    owner_user_id = uuid4()

    organization = await service.create_organization(
        payload=OrganizationCreate(name="Test Org", slug="test-org"),
        owner_user_id=owner_user_id,
    )

    assert organization.slug == "test-org"
    assert repository.memberships[0].organization_id == organization.id
    assert repository.memberships[0].user_id == owner_user_id
    assert repository.memberships[0].role == ORGANIZATION_OWNER_ROLE


@pytest.mark.asyncio
async def test_create_organization_rejects_duplicate_slug() -> None:
    repository = FakeOrganizationRepository()
    service = OrganizationService(repository)  # type: ignore[arg-type]
    owner_user_id = uuid4()

    await service.create_organization(
        payload=OrganizationCreate(name="Test Org", slug="test-org"),
        owner_user_id=owner_user_id,
    )

    with pytest.raises(OrganizationSlugAlreadyExistsError):
        await service.create_organization(
            payload=OrganizationCreate(name="Other Org", slug="test-org"),
            owner_user_id=owner_user_id,
        )


@pytest.mark.asyncio
async def test_ensure_user_is_member_rejects_non_member() -> None:
    repository = FakeOrganizationRepository()
    service = OrganizationService(repository)  # type: ignore[arg-type]

    with pytest.raises(OrganizationAccessDeniedError):
        await service.ensure_user_is_member(
            organization_id=uuid4(),
            user_id=uuid4(),
        )
