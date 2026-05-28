from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.auth.dependencies import CurrentUserDependency
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationMemberRead,
    OrganizationRead,
)
from app.modules.organizations.service import (
    OrganizationAccessDeniedError,
    OrganizationService,
    OrganizationSlugAlreadyExistsError,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])

DatabaseSessionDependency = Annotated[AsyncSession, Depends(get_database_session)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OrganizationCreate,
    current_user: CurrentUserDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = OrganizationRepository(session)
    service = OrganizationService(repository)

    try:
        organization = await service.create_organization(
            payload=payload,
            owner_user_id=current_user.id,
        )
    except OrganizationSlugAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists.",
        ) from exc

    await session.commit()

    return success_response(data=OrganizationRead.model_validate(organization).model_dump())


@router.get("")
async def list_organizations(
    current_user: CurrentUserDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = OrganizationRepository(session)
    service = OrganizationService(repository)

    organizations = await service.list_user_organizations(current_user.id)

    return success_response(
        data=[
            OrganizationRead.model_validate(organization).model_dump()
            for organization in organizations
        ]
    )


@router.get("/{organization_id}/members")
async def list_organization_members(
    organization_id: UUID,
    current_user: CurrentUserDependency,
    session: DatabaseSessionDependency,
) -> dict[str, object]:
    repository = OrganizationRepository(session)
    service = OrganizationService(repository)

    try:
        members = await service.list_organization_members(
            organization_id=organization_id,
            requester_user_id=current_user.id,
        )
    except OrganizationAccessDeniedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        ) from exc

    return success_response(
        data=[OrganizationMemberRead.model_validate(member).model_dump() for member in members]
    )
