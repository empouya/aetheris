import hashlib
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage.service import ObjectStorageService
from app.modules.documents.models import Document, DocumentStatus, JobStatus, JobType, ProcessingJob
from app.modules.documents.repository import DocumentRepository, ProcessingJobRepository
from app.workers.ingestion import process_document

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


class DocumentService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        document_repository: DocumentRepository,
        job_repository: ProcessingJobRepository,
        storage_service: ObjectStorageService,
    ) -> None:
        self.session = session
        self.document_repository = document_repository
        self.job_repository = job_repository
        self.storage_service = storage_service

    async def upload_document(
        self,
        *,
        organization_id: UUID,
        uploaded_by_user_id: UUID | None,
        filename: str,
        content_type: str,
        data: bytes,
    ) -> tuple[Document, ProcessingJob]:
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedFileTypeError(
                f"Content type '{content_type}' is not supported. "
                f"Allowed types: {sorted(ALLOWED_CONTENT_TYPES)}"
            )

        if len(data) > MAX_FILE_SIZE_BYTES:
            raise FileTooLargeError(
                f"File size {len(data)} bytes exceeds the maximum allowed "
                f"size of {MAX_FILE_SIZE_BYTES} bytes."
            )

        checksum = hashlib.sha256(data).hexdigest()
        document_id = uuid4()
        object_path = f"{organization_id}/{document_id}/{filename}"
        now = datetime.now(UTC)

        await self.storage_service.upload_file(
            object_path=object_path,
            data=data,
            content_type=content_type,
        )

        document = await self.document_repository.add(
            Document(
                id=document_id,
                organization_id=organization_id,
                uploaded_by_user_id=uploaded_by_user_id,
                filename=filename,
                content_type=content_type,
                file_size=len(data),
                object_storage_path=object_path,
                checksum=checksum,
                status=DocumentStatus.UPLOADED,
                created_at=now,
                updated_at=now,
            )
        )

        job = await self.job_repository.add(
            ProcessingJob(
                id=uuid4(),
                organization_id=organization_id,
                document_id=document_id,
                job_type=JobType.INGESTION,
                status=JobStatus.QUEUED,
                retry_count=0,
                created_at=now,
            )
        )

        cast(Any, process_document).delay(
            document_id=str(document_id),
            job_id=str(job.id),
            organization_id=str(organization_id),
        )

        return document, job
