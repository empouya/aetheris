from uuid import UUID, uuid4

import pytest
from app.modules.documents.models import Document, DocumentStatus, JobStatus, JobType, ProcessingJob
from app.modules.documents.service import (
    MAX_FILE_SIZE_BYTES,
    DocumentService,
    FileTooLargeError,
    UnsupportedFileTypeError,
)


class FakeDocumentRepository:
    def __init__(self) -> None:
        self.documents: list[Document] = []

    async def add(self, document: Document) -> Document:
        self.documents.append(document)
        return document

    async def get_by_id(self, *, document_id: UUID, organization_id: UUID) -> Document | None:
        for document in self.documents:
            if document.id == document_id and document.organization_id == organization_id:
                return document
        return None

    async def list_for_organization(self, organization_id: UUID) -> list[Document]:
        return [d for d in self.documents if d.organization_id == organization_id]


class FakeProcessingJobRepository:
    def __init__(self) -> None:
        self.jobs: list[ProcessingJob] = []

    async def add(self, job: ProcessingJob) -> ProcessingJob:
        self.jobs.append(job)
        return job

    async def get_by_id(self, *, job_id: UUID, organization_id: UUID) -> ProcessingJob | None:
        for job in self.jobs:
            if job.id == job_id and job.organization_id == organization_id:
                return job
        return None

    async def list_for_organization(self, organization_id: UUID) -> list[ProcessingJob]:
        return [j for j in self.jobs if j.organization_id == organization_id]


class FakeObjectStorageService:
    def __init__(self) -> None:
        self.uploaded: list[str] = []

    async def upload_file(self, *, object_path: str, data: bytes, content_type: str) -> str:
        self.uploaded.append(object_path)
        return object_path


class FakeSession:
    async def flush(self) -> None:
        pass


def make_service(
    document_repository: FakeDocumentRepository,
    job_repository: FakeProcessingJobRepository,
    storage_service: FakeObjectStorageService,
) -> DocumentService:
    return DocumentService(
        session=FakeSession(),  # type: ignore[arg-type]
        document_repository=document_repository,  # type: ignore[arg-type]
        job_repository=job_repository,  # type: ignore[arg-type]
        storage_service=storage_service,  # type: ignore[arg-type]
    )


@pytest.mark.asyncio
async def test_upload_document_creates_document_and_job() -> None:
    organization_id = uuid4()
    user_id = uuid4()
    document_repo = FakeDocumentRepository()
    job_repo = FakeProcessingJobRepository()
    storage = FakeObjectStorageService()

    service = make_service(document_repo, job_repo, storage)

    document, job = await service.upload_document(
        organization_id=organization_id,
        uploaded_by_user_id=user_id,
        filename="test.txt",
        content_type="text/plain",
        data=b"hello world",
    )

    assert document.organization_id == organization_id
    assert document.uploaded_by_user_id == user_id
    assert document.filename == "test.txt"
    assert document.content_type == "text/plain"
    assert document.file_size == len(b"hello world")
    assert document.status == DocumentStatus.UPLOADED
    assert document.checksum != ""

    assert job.organization_id == organization_id
    assert job.document_id == document.id
    assert job.job_type == JobType.INGESTION
    assert job.status == JobStatus.QUEUED
    assert job.retry_count == 0

    assert len(document_repo.documents) == 1
    assert len(job_repo.jobs) == 1
    assert len(storage.uploaded) == 1


@pytest.mark.asyncio
async def test_upload_document_object_path_is_tenant_scoped() -> None:
    organization_id = uuid4()
    document_repo = FakeDocumentRepository()
    job_repo = FakeProcessingJobRepository()
    storage = FakeObjectStorageService()

    service = make_service(document_repo, job_repo, storage)

    document, _ = await service.upload_document(
        organization_id=organization_id,
        uploaded_by_user_id=None,
        filename="report.pdf",
        content_type="application/pdf",
        data=b"pdf content",
    )

    assert storage.uploaded[0].startswith(str(organization_id))
    assert str(document.id) in storage.uploaded[0]
    assert "report.pdf" in storage.uploaded[0]


@pytest.mark.asyncio
async def test_upload_document_rejects_unsupported_content_type() -> None:
    service = make_service(
        FakeDocumentRepository(),
        FakeProcessingJobRepository(),
        FakeObjectStorageService(),
    )

    with pytest.raises(UnsupportedFileTypeError):
        await service.upload_document(
            organization_id=uuid4(),
            uploaded_by_user_id=None,
            filename="image.png",
            content_type="image/png",
            data=b"fake image",
        )


@pytest.mark.asyncio
async def test_upload_document_rejects_oversized_file() -> None:
    service = make_service(
        FakeDocumentRepository(),
        FakeProcessingJobRepository(),
        FakeObjectStorageService(),
    )

    oversized_data = b"x" * (MAX_FILE_SIZE_BYTES + 1)

    with pytest.raises(FileTooLargeError):
        await service.upload_document(
            organization_id=uuid4(),
            uploaded_by_user_id=None,
            filename="large.txt",
            content_type="text/plain",
            data=oversized_data,
        )


@pytest.mark.asyncio
async def test_upload_document_does_not_store_to_object_storage_on_validation_failure() -> None:
    storage = FakeObjectStorageService()
    service = make_service(
        FakeDocumentRepository(),
        FakeProcessingJobRepository(),
        storage,
    )

    with pytest.raises(UnsupportedFileTypeError):
        await service.upload_document(
            organization_id=uuid4(),
            uploaded_by_user_id=None,
            filename="bad.exe",
            content_type="application/octet-stream",
            data=b"bad content",
        )

    assert len(storage.uploaded) == 0
