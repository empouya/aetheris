from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from app.core.security import hash_token
from app.modules.api_keys.models import ApiKey
from app.modules.api_keys.schemas import ApiKeyCreate
from app.modules.api_keys.service import API_KEY_PREFIX, ApiKeyService
from app.modules.organizations.models import Membership
from app.modules.organizations.service import OrganizationAccessDeniedError


class FakeApiKeyRepository:
    def __init__(self) -> None:
        self.api_keys: list[ApiKey] = []

    async def add(self, api_key: ApiKey) -> ApiKey:
        self.api_keys.append(api_key)
        return api_key

    async def list_for_organization(self, organization_id: UUID) -> list[ApiKey]:
        return [api_key for api_key in self.api_keys if api_key.organization_id == organization_id]

    async def get_for_organization(
        self,
        *,
        api_key_id: UUID,
        organization_id: UUID,
    ) -> ApiKey | None:
        for api_key in self.api_keys:
            if api_key.id == api_key_id and api_key.organization_id == organization_id:
                return api_key
        return None


class FakeOrganizationRepository:
    def __init__(self, membership: Membership | None) -> None:
        self.membership = membership

    async def get_membership(
        self,
        *,
        organization_id: UUID,
        user_id: UUID,
    ) -> Membership | None:
        if (
            self.membership is not None
            and self.membership.organization_id == organization_id
            and self.membership.user_id == user_id
        ):
            return self.membership
        return None


@pytest.mark.asyncio
async def test_create_api_key_hashes_plaintext_key() -> None:
    organization_id = uuid4()
    user_id = uuid4()
    membership = Membership(
        organization_id=organization_id,
        user_id=user_id,
        role="owner",
        created_at=datetime.now(UTC),
    )

    repository = FakeApiKeyRepository()
    service = ApiKeyService(
        repository=repository,  # type: ignore[arg-type]
        organization_repository=FakeOrganizationRepository(membership),  # type: ignore[arg-type]
    )

    api_key, plaintext_key = await service.create_api_key(
        payload=ApiKeyCreate(organization_id=organization_id, name="Test Key"),
        requester_user_id=user_id,
    )

    assert plaintext_key.startswith(f"{API_KEY_PREFIX}_")
    assert api_key.key_hash == hash_token(plaintext_key)
    assert api_key.key_hash != plaintext_key
    assert api_key.key_prefix == plaintext_key[:24]


@pytest.mark.asyncio
async def test_create_api_key_rejects_non_member() -> None:
    service = ApiKeyService(
        repository=FakeApiKeyRepository(),  # type: ignore[arg-type]
        organization_repository=FakeOrganizationRepository(None),  # type: ignore[arg-type]
    )

    with pytest.raises(OrganizationAccessDeniedError):
        await service.create_api_key(
            payload=ApiKeyCreate(organization_id=uuid4(), name="Test Key"),
            requester_user_id=uuid4(),
        )
