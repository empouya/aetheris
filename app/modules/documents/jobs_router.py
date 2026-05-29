from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.auth.dependencies import CurrentTenantContextDependency
from app.modules.documents.repository import ProcessingJobRepository
from app.modules.documents.schemas import ProcessingJobRead

router = APIRouter(prefix="/jobs", tags=["jobs"])

DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]


@router.get("/{job_id}")
async def get_job(
    job_id: UUID,
    tenant_context: CurrentTenantContextDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = ProcessingJobRepository(session)

    job = await repository.get_by_id(
        job_id=job_id,
        organization_id=tenant_context.organization_id,
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    return success_response(data=ProcessingJobRead.model_validate(job).model_dump())
