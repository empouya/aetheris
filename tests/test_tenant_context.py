from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest
from app.core.security import generate_secure_token, hash_token
from app.modules.api_keys.models import ApiKey
from app.modules.auth.dependencies import get_current_api_key_context
from fastapi import HTTPException


class FakeSession:
    async def flush(self) -> None:
        pass


@pytest.mark.asyncio
async def test_api_key_context_resolves_organization(monkeypatch: pytest.MonkeyPatch) -> None:
    organization_id = uuid4()
    plaintext_key = f"athr_live_{generate_secure_token()}"
    api_key = ApiKey(
        organization_id=organization_id,
        name="Test Key",
        key_prefix=plaintext_key[:24],
        key_hash=hash_token(plaintext_key),
        last_used_at=None,
        revoked_at=None,
        created_at=datetime.now(UTC),
    )

    async def fake_get_active_by_prefix(self: Any, key_prefix: str) -> list[ApiKey]:
        assert key_prefix == plaintext_key[:24]
        return [api_key]

    monkeypatch.setattr(
        "app.modules.api_keys.repository.ApiKeyRepository.get_active_by_prefix",
        fake_get_active_by_prefix,
    )

    context = await get_current_api_key_context(
        token=plaintext_key,
        session=FakeSession(),  # type: ignore[arg-type]
    )

    assert context.organization_id == organization_id
    assert context.principal_type == "api_key"
    assert context.api_key_id == api_key.id
    assert api_key.last_used_at is not None


@pytest.mark.asyncio
async def test_api_key_context_rejects_invalid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get_active_by_prefix(self: Any, key_prefix: str) -> list[ApiKey]:
        return []

    monkeypatch.setattr(
        "app.modules.api_keys.repository.ApiKeyRepository.get_active_by_prefix",
        fake_get_active_by_prefix,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_api_key_context(
            token=f"athr_live_{generate_secure_token()}",
            session=FakeSession(),  # type: ignore[arg-type]
        )

    assert exc_info.value.status_code == 401
