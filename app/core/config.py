from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="AETHERIS_",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Literal["development", "testing", "staging", "production"] = "development"
    debug: bool = False
    project_name: str = "Aetheris API"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[AnyHttpUrl] = []

    database_url: str = ""
    redis_url: str = ""
    qdrant_url: str = ""

    minio_endpoint: str = ""
    minio_access_key: str = ""
    minio_secret_key: str = ""
    minio_secure: bool = False
    minio_bucket: str = ""

    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    refresh_token_expire_days: int = 30

    cohere_api_key: str = ""

    @model_validator(mode="after")
    def validate_required_runtime_settings(self) -> "Settings":
        required_fields = {
            "database_url": self.database_url,
            "redis_url": self.redis_url,
            "qdrant_url": self.qdrant_url,
            "minio_endpoint": self.minio_endpoint,
            "minio_access_key": self.minio_access_key,
            "minio_secret_key": self.minio_secret_key,
            "minio_bucket": self.minio_bucket,
            "jwt_secret_key": self.jwt_secret_key,
            "cohere_api_key": self.cohere_api_key,
        }

        missing_fields = [name for name, value in required_fields.items() if not value]

        if missing_fields:
            missing_names = ", ".join(missing_fields)
            raise ValueError(f"Missing required runtime settings: {missing_names}")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
