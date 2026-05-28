from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_database_session
from app.core.security import hash_token
from app.modules.api_keys.models import ApiKey
from app.modules.api_keys.repository import ApiKeyRepository
from app.modules.auth.context import AuthenticatedTenantContext
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.organizations.repository import OrganizationRepository

bearer_scheme = HTTPBearer(auto_error=False)


DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
BearerCredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]
OrganizationIdQueryDependency = Annotated[UUID | None, Query()]


def decode_jwt(token: str, secret_key: str, algorithm: str) -> dict[str, object]:
    return jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token,
        secret_key,
        algorithms=[algorithm],
    )


def is_api_key_token(token: str) -> bool:
    return token.startswith("athr_live_")


async def get_current_api_key_context(
    *,
    token: str,
    session: AsyncSession,
) -> AuthenticatedTenantContext:
    key_prefix = token[:24]
    token_hash = hash_token(token)

    repository = ApiKeyRepository(session)
    candidates = await repository.get_active_by_prefix(key_prefix)

    matching_key: ApiKey | None = None
    for candidate in candidates:
        if candidate.key_hash == token_hash:
            matching_key = candidate
            break

    if matching_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    await repository.mark_used(matching_key)

    return AuthenticatedTenantContext(
        organization_id=matching_key.organization_id,
        principal_type="api_key",
        user=None,
        api_key_id=matching_key.id,
    )


async def get_current_user_tenant_context(
    *,
    organization_id: UUID,
    user: User,
    session: AsyncSession,
) -> AuthenticatedTenantContext:
    organization_repository = OrganizationRepository(session)
    membership = await organization_repository.get_membership(
        organization_id=organization_id,
        user_id=user.id,
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )

    return AuthenticatedTenantContext(
        organization_id=organization_id,
        principal_type="user",
        user=user,
        api_key_id=None,
    )


async def get_current_user_from_token(
    *,
    token: str,
    session: AsyncSession,
    settings: Settings,
) -> User:
    try:
        payload = decode_jwt(
            token,
            settings.jwt_secret_key,
            settings.jwt_algorithm,
        )
        token_type = payload.get("type")
        subject = payload.get("sub")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        ) from exc

    if token_type != "access" or not isinstance(subject, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    repository = UserRepository(session)
    user = await repository.get_by_id(UUID(subject))

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        )

    return user


async def get_current_user(
    request: Request,
    credentials: BearerCredentialsDependency,
    session: DatabaseSessionDependency,
    settings: SettingsDependency,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    user = await get_current_user_from_token(
        token=credentials.credentials,
        session=session,
        settings=settings,
    )

    request.state.user_id = str(user.id)
    return user


async def get_authenticated_tenant_context(
    credentials: BearerCredentialsDependency,
    session: DatabaseSessionDependency,
    settings: SettingsDependency,
    organization_id: OrganizationIdQueryDependency = None,
) -> AuthenticatedTenantContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    token = credentials.credentials

    if is_api_key_token(token):
        context = await get_current_api_key_context(token=token, session=session)

        if organization_id is not None and organization_id != context.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied.",
            )

        await session.commit()
        return context

    user = await get_current_user_from_token(
        token=token,
        session=session,
        settings=settings,
    )

    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required.",
        )

    return await get_current_user_tenant_context(
        organization_id=organization_id,
        user=user,
        session=session,
    )


CurrentTenantContextDependency = Annotated[
    AuthenticatedTenantContext,
    Depends(get_authenticated_tenant_context),
]

CurrentUserDependency = Annotated[User, Depends(get_current_user)]
