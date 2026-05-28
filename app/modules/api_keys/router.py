from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.api_keys.repository import ApiKeyRepository
from app.modules.api_keys.schemas import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyRead
from app.modules.api_keys.service import ApiKeyNotFoundError, ApiKeyService
from app.modules.auth.dependencies import CurrentTenantContextDependency, CurrentUserDependency
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.service import OrganizationAccessDeniedError

router = APIRouter(prefix="/api-keys", tags=["api-keys"])

DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]
OrganizationIdQuery = Annotated[UUID, Query(...)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    payload: ApiKeyCreate,
    current_user: CurrentUserDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    service = ApiKeyService(
        repository=ApiKeyRepository(session),
        organization_repository=OrganizationRepository(session),
    )

    try:
        api_key, plaintext_key = await service.create_api_key(
            payload=payload,
            requester_user_id=current_user.id,
        )
    except OrganizationAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        ) from exc

    await session.commit()

    return success_response(
        data=ApiKeyCreateResponse(
            id=api_key.id,
            organization_id=api_key.organization_id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            api_key=plaintext_key,
            created_at=api_key.created_at,
        ).model_dump()
    )


@router.get("")
async def list_api_keys(
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
    organization_id: OrganizationIdQuery,
) -> dict[str, object]:
    if tenant_context.user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User authentication required.",
        )

    service = ApiKeyService(
        repository=ApiKeyRepository(session),
        organization_repository=OrganizationRepository(session),
    )

    try:
        api_keys = await service.list_api_keys(
            organization_id=organization_id,
            requester_user_id=tenant_context.user.id,
        )
    except OrganizationAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        ) from exc

    return success_response(
        data=[ApiKeyRead.model_validate(api_key).model_dump() for api_key in api_keys]
    )


@router.delete("/{api_key_id}")
async def revoke_api_key(
    api_key_id: UUID,
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
    organization_id: OrganizationIdQuery,
) -> dict[str, object]:
    if tenant_context.user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User authentication required.",
        )

    service = ApiKeyService(
        repository=ApiKeyRepository(session),
        organization_repository=OrganizationRepository(session),
    )

    try:
        await service.revoke_api_key(
            api_key_id=api_key_id,
            organization_id=organization_id,
            requester_user_id=tenant_context.user.id,
        )
    except OrganizationAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        ) from exc
    except ApiKeyNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found.",
        ) from exc

    await session.commit()

    return success_response(data={"revoked": True})
