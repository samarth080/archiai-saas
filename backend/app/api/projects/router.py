from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.project import ActivityLogOut, ProjectCreate, ProjectOut, ProjectUpdate, ProjectVersionOut
from app.services.auth_service import get_current_user
from app.services.project_service import (
    create_project,
    delete_project,
    duplicate_project,
    get_project,
    list_project_activity,
    list_project_versions,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])
bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return user.id


@router.post("", response_model=ProjectOut, status_code=201)
async def create(
    data: ProjectCreate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_project(db, user_id, data)


@router.get("", response_model=list[ProjectOut])
async def list_all(
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_projects(db, user_id)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_one(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_project(db, user_id, project_id)


@router.get("/{project_id}/versions", response_model=list[ProjectVersionOut])
async def versions(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_project_versions(db, user_id, project_id)


@router.post("/{project_id}/duplicate", response_model=ProjectOut, status_code=201)
async def duplicate(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await duplicate_project(db, user_id, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
async def update(
    project_id: str,
    data: ProjectUpdate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_project(db, user_id, project_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_project(db, user_id, project_id)


@router.get("/{project_id}/activity", response_model=list[ActivityLogOut])
async def activity(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_project_activity(db, user_id, project_id)
