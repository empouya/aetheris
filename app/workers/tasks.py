# pyright: reportUnknownMemberType=false, reportUntypedFunctionDecorator=false

from app.workers.celery_app import celery_app


@celery_app.task(name="aetheris.diagnostic.ping")
def diagnostic_ping() -> str:
    return "pong"
