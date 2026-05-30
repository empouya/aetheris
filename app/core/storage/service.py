import asyncio
from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error


class ObjectStorageError(Exception):
    pass


class ObjectStorageService:
    def __init__(self, client: Minio, bucket_name: str) -> None:
        self._client = client
        self._bucket_name = bucket_name

    async def ensure_bucket_exists(self) -> None:
        try:
            exists = await asyncio.to_thread(self._client.bucket_exists, self._bucket_name)
            if not exists:
                await asyncio.to_thread(self._client.make_bucket, self._bucket_name)
        except S3Error as exc:
            raise ObjectStorageError(
                f"Failed to ensure bucket '{self._bucket_name}' exists: {exc}"
            ) from exc

    async def upload_file(
        self,
        *,
        object_path: str,
        data: bytes,
        content_type: str,
    ) -> str:
        stream = BytesIO(data)
        length = len(data)
        try:
            await asyncio.to_thread(
                self._client.put_object,
                self._bucket_name,
                object_path,
                stream,
                length,
                content_type=content_type,
            )
        except S3Error as exc:
            raise ObjectStorageError(f"Failed to upload object '{object_path}': {exc}") from exc
        return object_path

    async def download_file(self, *, object_path: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                self._bucket_name,
                object_path,
            )
            data = await asyncio.to_thread(response.read)
            await asyncio.to_thread(response.close)
            await asyncio.to_thread(response.release_conn)
            return data
        except S3Error as exc:
            raise ObjectStorageError(f"Failed to download object '{object_path}': {exc}") from exc

    async def get_presigned_url(
        self,
        *,
        object_path: str,
        expires_in_seconds: int = 3600,
    ) -> str:
        try:
            url = await asyncio.to_thread(
                self._client.presigned_get_object,
                self._bucket_name,
                object_path,
                expires=timedelta(seconds=expires_in_seconds),
            )
        except S3Error as exc:
            raise ObjectStorageError(
                f"Failed to generate presigned URL for '{object_path}': {exc}"
            ) from exc
        return url

    async def delete_file(self, *, object_path: str) -> None:
        try:
            await asyncio.to_thread(self._client.remove_object, self._bucket_name, object_path)
        except S3Error as exc:
            raise ObjectStorageError(f"Failed to delete object '{object_path}': {exc}") from exc
