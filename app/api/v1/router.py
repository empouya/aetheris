from typing import Any

from fastapi import APIRouter, Response, status

from app.core.readiness import collect_readiness
from app.core.responses import success_response

router = APIRouter()


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
