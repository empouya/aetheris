from uuid import uuid4

import jwt
from app.core.config import get_settings
from app.modules.auth.tokens import create_access_token


def test_create_access_token_contains_user_subject() -> None:
    settings = get_settings()
    user_id = uuid4()

    token, expires_in = create_access_token(settings=settings, user_id=user_id)

    payload = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert expires_in == settings.access_token_expire_minutes * 60
