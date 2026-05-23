from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.utils.activity import log_activity


async def create_project(
    db: AsyncSession, user_id: str, data: ProjectCreate
) -> ProjectOut:
    project = Project(user_id=user_id, title=data.title, description=data.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    await log_activity(db, user_id, "project.created")
    return ProjectOut.model_validate(project)


async def list_projects(db: AsyncSession, user_id: str) -> list[ProjectOut]:
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    projects = result.scalars().all()
    return [ProjectOut.model_validate(p) for p in projects]


async def get_project(
    db: AsyncSession, user_id: str, project_id: str
) -> ProjectOut:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return ProjectOut.model_validate(project)


async def update_project(
    db: AsyncSession, user_id: str, project_id: str, data: ProjectUpdate
) -> ProjectOut:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    if data.title is not None:
        project.title = data.title
    if data.description is not None:
        project.description = data.description
    await db.commit()
    await db.refresh(project)
    await log_activity(db, user_id, "project.updated")
    return ProjectOut.model_validate(project)


async def delete_project(
    db: AsyncSession, user_id: str, project_id: str
) -> None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    await db.delete(project)
    await db.commit()
    await log_activity(db, user_id, "project.deleted")
