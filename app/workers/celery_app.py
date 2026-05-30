# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "aetheris",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks", "app.workers.ingestion"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)
