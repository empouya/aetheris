from io import BytesIO

from pypdf import PdfReader

from app.core.storage.service import ObjectStorageService

SUPPORTED_TEXT_TYPES = {"text/plain", "text/markdown"}
PDF_CONTENT_TYPE = "application/pdf"


class ExtractionError(Exception):
    pass


class TextExtractor:
    def __init__(self, storage_service: ObjectStorageService) -> None:
        self.storage_service = storage_service

    async def extract(self, *, object_path: str, content_type: str) -> str:
        try:
            data = await self.storage_service.download_file(object_path=object_path)
        except Exception as exc:
            raise ExtractionError(f"Failed to retrieve file from storage: {object_path}") from exc

        if content_type == PDF_CONTENT_TYPE:
            return self._extract_pdf(data)

        if content_type in SUPPORTED_TEXT_TYPES:
            return self._extract_text(data)

        raise ExtractionError(f"Unsupported content type for extraction: '{content_type}'")

    def _extract_pdf(self, data: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(data))
            pages = [page.extract_text() or "" for page in reader.pages]
            return "\n".join(pages).strip()
        except Exception as exc:
            raise ExtractionError("Failed to parse PDF content.") from exc

    def _extract_text(self, data: bytes) -> str:
        try:
            return data.decode("utf-8").strip()
        except UnicodeDecodeError as exc:
            raise ExtractionError("Failed to decode file as UTF-8 text.") from exc
