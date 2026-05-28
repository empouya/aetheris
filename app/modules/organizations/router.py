from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_database_session
from app.core.responses import success_response
from app.modules.auth.dependencies import CurrentUserDependency
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import OrganizationCreate, OrganizationRead
from app.modules.organizations.service import (
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
