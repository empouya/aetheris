from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginRequest
from app.modules.auth.service import AuthenticationFailedError, UserAccountService
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

    return success_response(
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        }
    )
