from typing import Any

from fastapi import APIRouter, Response, status

from app.core.readiness import collect_readiness
from app.core.responses import success_response
from app.modules.api_keys.router import router as api_keys_router
from app.modules.auth.router import router as auth_router
from app.modules.organizations.router import router as organizations_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(organizations_router)
router.include_router(api_keys_router)


@router.get("/health")
async def health() -> dict[str, object]:
    return success_response(
        data={
            "status": "ok",
            "service": "aetheris-api",
        }
    )


@router.get("/ready")
async def ready(response: Response) -> dict[str, Any]:
    readiness = await collect_readiness()

    if readiness["status"] != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return success_response(data=readiness)
