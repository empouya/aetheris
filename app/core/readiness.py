import asyncio
from typing import Any
from urllib.parse import urlparse

from minio import Minio
from qdrant_client import AsyncQdrantClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import async_session_factory


async def check_postgres() -> bool:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_redis() -> bool:
    settings = get_settings()

    try:
        parsed_url = urlparse(settings.redis_url)
        host = parsed_url.hostname
        port = parsed_url.port or 6379

        if host is None:
            return False

        reader, writer = await asyncio.open_connection(host, port)
        writer.write(b"*1\r\n$4\r\nPING\r\n")
        await writer.drain()

        response = await reader.readline()
        writer.close()
        await writer.wait_closed()

        return response.startswith(b"+PONG")
    except Exception:
        return False


async def check_qdrant() -> bool:
    settings = get_settings()
    client = AsyncQdrantClient(url=settings.qdrant_url)
    try:
        await client.get_collections()
        return True
    except Exception:
        return False
    finally:
        await client.close()


def _check_minio_sync() -> bool:
    settings = get_settings()
    client = Minio(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )

    try:
        client.bucket_exists(settings.minio_bucket)
        return True
    except Exception:
        return False


async def check_minio() -> bool:
    return await asyncio.to_thread(_check_minio_sync)


async def collect_readiness() -> dict[str, Any]:
    checks = {
        "postgres": await check_postgres(),
        "redis": await check_redis(),
        "qdrant": await check_qdrant(),
        "minio": await check_minio(),
    }

    return {
        "status": "ready" if all(checks.values()) else "not_ready",
        "checks": checks,
    }
