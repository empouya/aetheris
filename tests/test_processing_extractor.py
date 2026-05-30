import pytest
from app.modules.processing.extractor import ExtractionError, TextExtractor


class FakeObjectStorageService:
    def __init__(self, data: bytes) -> None:
        self._data = data

    async def download_file(self, *, object_path: str) -> bytes:
        return self._data


class FailingObjectStorageService:
    async def download_file(self, *, object_path: str) -> bytes:
        raise RuntimeError("Storage unavailable")


@pytest.mark.asyncio
async def test_extract_plain_text() -> None:
    content = b"Hello, this is a plain text document."
    extractor = TextExtractor(storage_service=FakeObjectStorageService(content))  # type: ignore[arg-type]

    result = await extractor.extract(
        object_path="org/doc/file.txt",
        content_type="text/plain",
    )

    assert result == "Hello, this is a plain text document."


@pytest.mark.asyncio
async def test_extract_markdown() -> None:
    content = b"# Title\n\nSome markdown content."
    extractor = TextExtractor(storage_service=FakeObjectStorageService(content))  # type: ignore[arg-type]

    result = await extractor.extract(
        object_path="org/doc/file.md",
        content_type="text/markdown",
    )

    assert result == "# Title\n\nSome markdown content."


@pytest.mark.asyncio
async def test_extract_raises_on_unsupported_type() -> None:
    extractor = TextExtractor(storage_service=FakeObjectStorageService(b"data"))  # type: ignore[arg-type]

    with pytest.raises(ExtractionError):
        await extractor.extract(
            object_path="org/doc/file.exe",
            content_type="application/octet-stream",
        )


@pytest.mark.asyncio
async def test_extract_raises_on_storage_failure() -> None:
    extractor = TextExtractor(storage_service=FailingObjectStorageService())  # type: ignore[arg-type]

    with pytest.raises(ExtractionError):
        await extractor.extract(
            object_path="org/doc/file.txt",
            content_type="text/plain",
        )


@pytest.mark.asyncio
async def test_extract_raises_on_invalid_utf8() -> None:
    extractor = TextExtractor(storage_service=FakeObjectStorageService(b"\xff\xfe"))  # type: ignore[arg-type]

    with pytest.raises(ExtractionError):
        await extractor.extract(
            object_path="org/doc/file.txt",
            content_type="text/plain",
        )
