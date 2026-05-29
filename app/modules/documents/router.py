from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import get_database_session
from app.core.responses import success_response
from app.core.storage.client import create_minio_client
from app.core.storage.service import ObjectStorageService
from app.modules.auth.dependencies import CurrentTenantContextDependency
from app.modules.documents.repository import DocumentRepository, ProcessingJobRepository
from app.modules.documents.schemas import DocumentRead, ProcessingJobRead
from app.modules.documents.service import (
    DocumentService,
    FileTooLargeError,
    UnsupportedFileTypeError,
)

router = APIRouter(prefix="/documents", tags=["documents"])

DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile,
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
    settings: SettingsDependency,
) -> dict[str, object]:
    data = await file.read()
    content_type = file.content_type or ""
    filename = file.filename or "untitled"

    storage_service = ObjectStorageService(
        client=create_minio_client(settings),
        bucket_name=settings.minio_bucket,
    )

    service = DocumentService(
        session=session,
        document_repository=DocumentRepository(session),
        job_repository=ProcessingJobRepository(session),
        storage_service=storage_service,
    )

    try:
        document, job = await service.upload_document(
            organization_id=tenant_context.organization_id,
            uploaded_by_user_id=tenant_context.user.id if tenant_context.user else None,
            filename=filename,
            content_type=content_type,
            data=data,
        )
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=str(exc),
        ) from exc
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc

    await session.commit()

    return success_response(
        data={
            "document": DocumentRead.model_validate(document).model_dump(),
            "job": ProcessingJobRead.model_validate(job).model_dump(),
        }
    )


@router.get("")
async def list_documents(
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = DocumentRepository(session)

    documents = await repository.list_for_organization(tenant_context.organization_id)

    return success_response(
        data=[DocumentRead.model_validate(document).model_dump() for document in documents]
    )


@router.get("/{document_id}")
async def get_document(
    document_id: UUID,
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = DocumentRepository(session)

    document = await repository.get_by_id(
        document_id=document_id,
        organization_id=tenant_context.organization_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return success_response(data=DocumentRead.model_validate(document).model_dump())
