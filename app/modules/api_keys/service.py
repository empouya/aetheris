from datetime import UTC, datetime
from uuid import UUID

from app.core.security import generate_secure_token, hash_token
from app.modules.api_keys.models import ApiKey
from app.modules.api_keys.repository import ApiKeyRepository
from app.modules.api_keys.schemas import ApiKeyCreate
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.service import OrganizationService

API_KEY_PREFIX = "athr_live"


class ApiKeyNotFoundError(Exception):
    pass


class ApiKeyService:
    def __init__(
        self,
        *,
        repository: ApiKeyRepository,
        organization_repository: OrganizationRepository,
    ) -> None:
        self.repository = repository
        self.organization_service = OrganizationService(organization_repository)

    async def create_api_key(
        self,
        *,
        payload: ApiKeyCreate,
        requester_user_id: UUID,
    ) -> tuple[ApiKey, str]:
        await self.organization_service.ensure_user_is_member(
            organization_id=payload.organization_id,
            user_id=requester_user_id,
        )

        now = datetime.now(UTC)
        secret = generate_secure_token()
        plaintext_key = f"{API_KEY_PREFIX}_{secret}"
        key_prefix = plaintext_key[:24]

        api_key = ApiKey(
            organization_id=payload.organization_id,
            name=payload.name.strip(),
            key_prefix=key_prefix,
            key_hash=hash_token(plaintext_key),
            last_used_at=None,
            revoked_at=None,
            created_at=now,
        )

        await self.repository.add(api_key)
        return api_key, plaintext_key

    async def list_api_keys(
        self,
        *,
        organization_id: UUID,
        requester_user_id: UUID,
    ) -> list[ApiKey]:
        await self.organization_service.ensure_user_is_member(
            organization_id=organization_id,
            user_id=requester_user_id,
        )
        return await self.repository.list_for_organization(organization_id)

    async def revoke_api_key(
        self,
        *,
        api_key_id: UUID,
        organization_id: UUID,
        requester_user_id: UUID,
    ) -> None:
        await self.organization_service.ensure_user_is_member(
            organization_id=organization_id,
            user_id=requester_user_id,
        )

        api_key = await self.repository.get_for_organization(
            api_key_id=api_key_id,
            organization_id=organization_id,
        )

        if api_key is None:
            raise ApiKeyNotFoundError("API key does not exist.")

        if api_key.revoked_at is None:
            api_key.revoked_at = datetime.now(UTC)
