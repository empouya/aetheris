from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import Settings


def encode_jwt(payload: dict[str, object], secret_key: str, algorithm: str) -> str:
    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload,
        secret_key,
        algorithm=algorithm,
    )


def create_access_token(
    *,
    settings: Settings,
    user_id: UUID,
    expires_delta: timedelta | None = None,
) -> tuple[str, int]:
    expires_in = int(
        (expires_delta or timedelta(minutes=settings.access_token_expire_minutes)).total_seconds()
    )
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=expires_in)

    payload: dict[str, object] = {
        "sub": str(user_id),
        "type": "access",
        "exp": expires_at,
        "iat": now,
    }

    token = encode_jwt(
        payload=payload,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, expires_in
