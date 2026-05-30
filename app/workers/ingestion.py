import asyncio
import json
import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

import cohere
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.core.registry  # noqa: F401  # type: ignore[reportUnusedImport]
from app.core.config import get_settings
from app.core.embeddings.service import EMBEDDING_MODEL, EmbeddingService
from app.core.qdrant.service import QdrantService, VectorPayload
from app.core.storage.client import create_minio_client
from app.core.storage.service import ObjectStorageService
from app.modules.documents.models import (
    Document,
    DocumentChunk,
    DocumentStatus,
    JobStatus,
    ProcessingJob,
)
from app.modules.documents.repository import (
    DocumentChunkRepository,
    DocumentRepository,
    ProcessingJobRepository,
)
from app.modules.processing.chunker import TextChunker
from app.modules.processing.extractor import TextExtractor
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _mark_processing(
    session: AsyncSession,
    document: Document,
    job: ProcessingJob,
) -> None:
    now = datetime.now(UTC)
    document.status = DocumentStatus.PROCESSING
    document.updated_at = now
    job.status = JobStatus.PROCESSING
    job.started_at = now
    await session.commit()


async def _mark_completed(
    session: AsyncSession,
    document: Document,
    job: ProcessingJob,
) -> None:
    now = datetime.now(UTC)
    document.status = DocumentStatus.READY
    document.updated_at = now
    job.status = JobStatus.COMPLETED
    job.completed_at = now
    await session.commit()


async def _mark_failed(
    session: AsyncSession,
    document: Document,
    job: ProcessingJob,
    error: str,
) -> None:
    now = datetime.now(UTC)
    document.status = DocumentStatus.FAILED
    document.updated_at = now
    job.status = JobStatus.FAILED
    job.error_message = error
    job.completed_at = now
    await session.commit()


async def _run_ingestion_pipeline(
    *,
    document_id: UUID,
    job_id: UUID,
    organization_id: UUID,
) -> None:
    settings = get_settings()

    storage_service = ObjectStorageService(
        client=create_minio_client(settings),
        bucket_name=settings.minio_bucket,
    )
    cohere_client = cohere.AsyncClientV2(api_key=settings.cohere_api_key)
    embedding_service = EmbeddingService(client=cohere_client)
    qdrant_service = QdrantService(client=QdrantClient(url=settings.qdrant_url))

    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            document_repo = DocumentRepository(session)
            job_repo = ProcessingJobRepository(session)
            chunk_repo = DocumentChunkRepository(session)

            document = await document_repo.get_by_id(
                document_id=document_id,
                organization_id=organization_id,
            )
            job = await job_repo.get_by_id(
                job_id=job_id,
                organization_id=organization_id,
            )

            if document is None or job is None:
                logger.error(
                    "process_document: document or job not found",
                    extra={
                        "document_id": str(document_id),
                        "job_id": str(job_id),
                    },
                )
                return

            await _mark_processing(session, document, job)

            try:
                text = await TextExtractor(storage_service=storage_service).extract(
                    object_path=document.object_storage_path,
                    content_type=document.content_type,
                )

                chunk_results = TextChunker().chunk(text)

                await chunk_repo.delete_by_document(
                    document_id=document_id,
                    organization_id=organization_id,
                )
                await qdrant_service.delete_by_document(
                    document_id=document_id,
                    organization_id=organization_id,
                )

                now = datetime.now(UTC)
                chunk_ids = [uuid4() for _ in chunk_results]
                vectors = await embedding_service.embed_texts([c.chunk_text for c in chunk_results])

                await chunk_repo.add_batch(
                    [
                        DocumentChunk(
                            id=chunk_ids[i],
                            organization_id=organization_id,
                            document_id=document_id,
                            chunk_index=chunk.chunk_index,
                            token_count=chunk.token_count,
                            text_hash=chunk.text_hash,
                            chunk_text=chunk.chunk_text,
                            metadata_json=json.dumps({}),
                            created_at=now,
                        )
                        for i, chunk in enumerate(chunk_results)
                    ]
                )

                await qdrant_service.upsert_vectors(
                    vectors=vectors,
                    payloads=[
                        VectorPayload(
                            chunk_id=chunk_ids[i],
                            organization_id=organization_id,
                            document_id=document_id,
                            chunk_index=chunk.chunk_index,
                            filename=document.filename,
                            embedding_model=EMBEDDING_MODEL,
                            created_at=now,
                        )
                        for i, chunk in enumerate(chunk_results)
                    ],
                )

                await _mark_completed(session, document, job)
                logger.info(
                    "process_document: completed",
                    extra={
                        "document_id": str(document_id),
                        "job_id": str(job_id),
                        "chunks": len(chunk_results),
                    },
                )

            except Exception as exc:
                await _mark_failed(session, document, job, error=str(exc))
                logger.error(
                    "process_document: failed",
                    extra={
                        "document_id": str(document_id),
                        "job_id": str(job_id),
                        "error": str(exc),
                    },
                )
    finally:
        await engine.dispose()


@celery_app.task(name="process_document", bind=True, max_retries=3)  # type: ignore[misc]
def process_document(
    self: object,
    *,
    document_id: str,
    job_id: str,
    organization_id: str,
) -> None:
    asyncio.run(
        _run_ingestion_pipeline(
            document_id=UUID(document_id),
            job_id=UUID(job_id),
            organization_id=UUID(organization_id),
        )
    )
