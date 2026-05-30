import cohere

EMBEDDING_MODEL = "embed-english-light-v3.0"
EMBEDDING_DIMENSIONS = 384


class EmbeddingError(Exception):
    pass


class EmbeddingService:
    def __init__(self, client: cohere.AsyncClientV2) -> None:
        self._client = client

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = await self._client.embed(
                model=EMBEDDING_MODEL,
                texts=texts,
                input_type="search_document",
                embedding_types=["float"],
            )
        except Exception as exc:
            raise EmbeddingError(f"Failed to generate embeddings for {len(texts)} texts.") from exc

        if response.embeddings.float_ is None:
            raise EmbeddingError("Cohere returned no float embeddings.")

        return [list(embedding) for embedding in response.embeddings.float_]
