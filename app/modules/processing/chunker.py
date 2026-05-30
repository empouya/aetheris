import hashlib
from dataclasses import dataclass

import tiktoken

ENCODING_NAME = "cl100k_base"
DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 64


@dataclass
class ChunkResult:
    chunk_index: int
    chunk_text: str
    token_count: int
    text_hash: str


class TextChunker:
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._encoding = tiktoken.get_encoding(ENCODING_NAME)

    def chunk(self, text: str) -> list[ChunkResult]:
        if not text.strip():
            return []

        tokens = self._encoding.encode(text)
        chunks: list[ChunkResult] = []
        start = 0
        index = 0

        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self._encoding.decode(chunk_tokens)
            text_hash = hashlib.sha256(chunk_text.encode()).hexdigest()

            chunks.append(
                ChunkResult(
                    chunk_index=index,
                    chunk_text=chunk_text,
                    token_count=len(chunk_tokens),
                    text_hash=text_hash,
                )
            )

            if end == len(tokens):
                break

            start += self.chunk_size - self.overlap
            index += 1

        return chunks
