import asyncio
from datetime import datetime
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from app.core.embeddings.service import EMBEDDING_DIMENSIONS

QDRANT_COLLECTION_NAME = "aetheris_chunks"


class QdrantError(Exception):
    pass


class VectorPayload:
    def __init__(
        self,
        *,
        chunk_id: UUID,
        organization_id: UUID,
        document_id: UUID,
        chunk_index: int,
        filename: str,
        embedding_model: str,
        created_at: datetime,
    ) -> None:
        self.chunk_id = chunk_id
        self.organization_id = organization_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.filename = filename
        self.embedding_model = embedding_model
        self.created_at = created_at


class QdrantService:
    def __init__(self, client: QdrantClient) -> None:
        self._client = client

    async def ensure_collection_exists(self) -> None:
        try:
            exists = await asyncio.to_thread(
                self._client.collection_exists,
                QDRANT_COLLECTION_NAME,
            )
            if not exists:
                await asyncio.to_thread(
                    self._client.create_collection,
                    QDRANT_COLLECTION_NAME,
                    vectors_config=qdrant_models.VectorParams(
                        size=EMBEDDING_DIMENSIONS,
                        distance=qdrant_models.Distance.COSINE,
                    ),
                )
        except Exception as exc:
            raise QdrantError(
                f"Failed to ensure collection '{QDRANT_COLLECTION_NAME}' exists."
            ) from exc

    async def upsert_vectors(
        self,
        *,
        vectors: list[list[float]],
        payloads: list[VectorPayload],
    ) -> None:
        if not vectors:
            return

        points = [
            qdrant_models.PointStruct(
                id=str(payload.chunk_id),
                vector=vector,
                payload={
                    "organization_id": str(payload.organization_id),
                    "document_id": str(payload.document_id),
                    "chunk_id": str(payload.chunk_id),
                    "chunk_index": payload.chunk_index,
                    "filename": payload.filename,
                    "embedding_model": payload.embedding_model,
                    "created_at": payload.created_at.isoformat(),
                },
            )
            for vector, payload in zip(vectors, payloads, strict=True)
        ]

        try:
            await asyncio.to_thread(
                self._client.upsert,
                collection_name=QDRANT_COLLECTION_NAME,
                points=points,
            )
        except Exception as exc:
            raise QdrantError("Failed to upsert vectors into Qdrant.") from exc

    async def delete_by_document(
        self,
        *,
        document_id: UUID,
        organization_id: UUID,
    ) -> None:
        try:
            await asyncio.to_thread(
                self._client.delete,
                collection_name=QDRANT_COLLECTION_NAME,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="organization_id",
                                match=qdrant_models.MatchValue(value=str(organization_id)),
                            ),
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=str(document_id)),
                            ),
                        ]
                    )
                ),
            )
        except Exception as exc:
            raise QdrantError(f"Failed to delete vectors for document '{document_id}'.") from exc
