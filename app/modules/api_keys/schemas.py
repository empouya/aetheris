from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    organization_id: UUID
    name: str = Field(min_length=1, max_length=255)


class ApiKeyCreateResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    key_prefix: str
    api_key: str
    created_at: datetime


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
