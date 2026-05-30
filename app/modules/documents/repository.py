from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import Document, DocumentChunk, ProcessingJob


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        return document

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

    async def list_for_organization(self, organization_id: UUID) -> list[Document]:
        result = await self.session.execute(
            select(Document)
            .where(
                Document.organization_id == organization_id,
                Document.deleted_at.is_(None),
            )
            .order_by(Document.created_at.desc())
        )
        return list(result.scalars().all())


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, job: ProcessingJob) -> ProcessingJob:
        self.session.add(job)
        await self.session.flush()
        return job

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

    async def list_for_organization(self, organization_id: UUID) -> list[ProcessingJob]:
        result = await self.session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.organization_id == organization_id)
            .order_by(ProcessingJob.created_at.desc())
        )
        return list(result.scalars().all())


class DocumentChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_batch(self, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        for chunk in chunks:
            self.session.add(chunk)
        await self.session.flush()
        return chunks

    async def get_by_document(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> list[DocumentChunk]:
        result = await self.session.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.organization_id == organization_id,
            )
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_by_document(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> None:
        chunks = await self.get_by_document(
            document_id=document_id,
            organization_id=organization_id,
        )
        for chunk in chunks:
            await self.session.delete(chunk)
        await self.session.flush()
