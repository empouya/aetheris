from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware
from app.core.storage.client import create_minio_client
from app.core.storage.service import ObjectStorageService


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    minio_client = create_minio_client(settings)
    storage_service = ObjectStorageService(
        client=minio_client,
        bucket_name=settings.minio_bucket,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        await storage_service.ensure_bucket_exists()
        yield

    app = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.middleware("http")(request_id_middleware)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
