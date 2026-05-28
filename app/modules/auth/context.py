from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.modules.auth.models import User

PrincipalType = Literal["user", "api_key"]


@dataclass(frozen=True)
class AuthenticatedTenantContext:
    organization_id: UUID
    principal_type: PrincipalType
    user: User | None = None
    api_key_id: UUID | None = None
