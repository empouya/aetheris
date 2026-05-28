from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_database_session
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]
BearerCredentialsDependency = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def decode_jwt(token: str, secret_key: str, algorithm: str) -> dict[str, object]:
    return jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token,
        secret_key,
        algorithms=[algorithm],
    )


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

    try:
        payload = decode_jwt(
            credentials.credentials,
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

    request.state.user_id = str(user.id)
    return user


CurrentUserDependency = Annotated[User, Depends(get_current_user)]
