import pytest
from app.core.config import Settings
from pydantic import ValidationError


def test_settings_require_runtime_dependencies() -> None:
    with pytest.raises(ValidationError, match="Missing required runtime settings"):
        Settings(
            database_url="",
            redis_url="",
            qdrant_url="",
            minio_endpoint="",
            minio_access_key="",
            minio_secret_key="",
            minio_bucket="",
        )


def test_settings_accept_runtime_dependencies() -> None:
    settings = Settings(
        database_url="postgresql+asyncpg://test:test@localhost:5432/test",
        redis_url="redis://localhost:6379/15",
        qdrant_url="http://localhost:6333",
        minio_endpoint="localhost:9000",
        minio_access_key="test",
        minio_secret_key="test",
        minio_bucket="test",
    )

    assert settings.environment == "testing"
    assert settings.database_url.startswith("postgresql+asyncpg://")
