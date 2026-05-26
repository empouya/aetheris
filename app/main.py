from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import request_id_middleware


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
        version="0.1.0",
    )

    app.middleware("http")(request_id_middleware)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
