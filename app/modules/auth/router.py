from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, LogoutRequest, RefreshTokenRequest
from app.modules.auth.service import (
    AuthenticationFailedError,
    InvalidRefreshTokenError,
    UserAccountService,
    UserNotFoundError,
)
from app.modules.auth.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/login")
async def login(
    payload: LoginRequest,
    session: DatabaseSessionDependency,
    settings: SettingsDependency,
) -> dict[str, object]:
    repository = UserRepository(session)
    service = UserAccountService(repository)

    try:
        user = await service.authenticate_user(payload.email, payload.password)
    except AuthenticationFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials.",
        ) from exc

    access_token, expires_in = create_access_token(settings=settings, user_id=user.id)
    refresh_token = await service.create_refresh_token(settings=settings, user_id=user.id)
    await session.commit()

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }
    )


@router.post("/refresh")
async def refresh_token(
    payload: RefreshTokenRequest,
    session: DatabaseSessionDependency,
    settings: SettingsDependency,
) -> dict[str, object]:
    repository = UserRepository(session)
    service = UserAccountService(repository)

    try:
        user, new_refresh_token = await service.rotate_refresh_token(
            settings=settings,
            refresh_token=payload.refresh_token,
        )
    except (InvalidRefreshTokenError, UserNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token.",
        ) from exc

    access_token, expires_in = create_access_token(settings=settings, user_id=user.id)
    await session.commit()

    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }
    )


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = UserRepository(session)
    service = UserAccountService(repository)

    await service.revoke_refresh_token(payload.refresh_token)
    await session.commit()

    return success_response(data={"revoked": True})
