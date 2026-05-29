from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, ProcessingJob


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, document: Document) -> None:
        self.session.add(document)
        await self.session.flush()

    async def get_by_id(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> Document | None:
        result = await self.session.execute(
            select(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, job: ProcessingJob) -> None:
        self.session.add(job)
        await self.session.flush()

    async def get_by_id(
        self,
        *,
        job_id: UUID,
        organization_id: UUID,
    ) -> ProcessingJob | None:
        result = await self.session.execute(
            select(ProcessingJob).where(
                ProcessingJob.id == job_id,
                ProcessingJob.organization_id == organization_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProcessingJob]:
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.organization_id == organization_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
