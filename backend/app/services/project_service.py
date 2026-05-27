from datetime import datetime, timezone
from copy import deepcopy

from fastapi import HTTPException
from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.design import Design
from app.models.design_version import DesignVersion
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate, ProjectVersionOut
from app.utils.activity import log_activity


async def _get_owned_project(db: AsyncSession, user_id: str, project_id: str) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return project


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
    result = await db.execute(
        select(Project).where(Project.user_id == user_id).order_by(desc(Project.updated_at))
    )
    projects = result.scalars().all()
    return [ProjectOut.model_validate(p) for p in projects]


async def get_project(
    db: AsyncSession, user_id: str, project_id: str
) -> ProjectOut:
    project = await _get_owned_project(db, user_id, project_id)
    return ProjectOut.model_validate(project)


async def update_project(
    db: AsyncSession, user_id: str, project_id: str, data: ProjectUpdate
) -> ProjectOut:
    project = await _get_owned_project(db, user_id, project_id)
    if data.title is not None:
        project.title = data.title
    if data.description is not None:
        project.description = data.description
    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)
    await log_activity(db, user_id, "project.updated")
    return ProjectOut.model_validate(project)


async def delete_project(
    db: AsyncSession, user_id: str, project_id: str
) -> None:
    project = await _get_owned_project(db, user_id, project_id)
    await db.execute(delete(DesignVersion).where(DesignVersion.project_id == project_id))
    await db.execute(delete(Design).where(Design.project_id == project_id))
    await db.delete(project)
    await db.commit()
    await log_activity(db, user_id, "project.deleted")


async def list_project_versions(
    db: AsyncSession, user_id: str, project_id: str
) -> list[ProjectVersionOut]:
    await _get_owned_project(db, user_id, project_id)
    result = await db.execute(
        select(DesignVersion)
        .where(DesignVersion.project_id == project_id)
        .order_by(desc(DesignVersion.created_at), desc(DesignVersion.version_number))
    )
    versions = result.scalars().all()
    return [
        ProjectVersionOut(
            id=version.id,
            design_id=version.design_id,
            project_id=version.project_id,
            version_number=version.version_number,
            version_name=version.version_name,
            version_type=version.version_type,
            change_summary=version.change_summary,
            created_by=version.user_id,
            created_at=version.created_at,
        )
        for version in versions
    ]


async def duplicate_project(
    db: AsyncSession, user_id: str, project_id: str
) -> ProjectOut:
    source = await _get_owned_project(db, user_id, project_id)
    duplicate = Project(
        user_id=user_id,
        title=f"Copy of {source.title}",
        description=source.description,
        thumbnail_url=source.thumbnail_url,
    )
    db.add(duplicate)
    await db.flush()

    design_result = await db.execute(
        select(Design)
        .where(Design.project_id == source.id, Design.user_id == user_id)
        .order_by(desc(Design.updated_at))
        .limit(1)
    )
    source_design = design_result.scalar_one_or_none()
    if source_design is not None:
        layout_json = deepcopy(source_design.layout_json)
        design = Design(
            project_id=duplicate.id,
            user_id=user_id,
            layout_json=layout_json,
        )
        db.add(design)
        await db.flush()
        version = DesignVersion(
            design_id=design.id,
            project_id=duplicate.id,
            user_id=user_id,
            version_number=1,
            version_name="Duplicated project",
            version_type="duplicate",
            change_summary=f"Copied from {source.title}",
            layout_json=deepcopy(layout_json),
        )
        db.add(version)

    duplicate.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(duplicate)
    await log_activity(db, user_id, "project.duplicated")
    return ProjectOut.model_validate(duplicate)
