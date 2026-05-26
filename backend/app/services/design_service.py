from fastapi import HTTPException
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.design import Design
from app.models.design_version import DesignVersion
from app.models.project import Project


async def save_generated_design(
    db: AsyncSession,
    user_id: str,
    project_id: str,
    layout_json: dict,
    prompt: str,
) -> tuple[Design, DesignVersion]:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    design = Design(project_id=project_id, user_id=user_id, layout_json=layout_json)
    db.add(design)
    await db.flush()

    version = DesignVersion(
        design_id=design.id,
        project_id=project_id,
        user_id=user_id,
        version_number=1,
        layout_json=layout_json,
        prompt_used=prompt,
    )
    db.add(version)
    await db.commit()
    await db.refresh(design)
    await db.refresh(version)
    return design, version


async def get_latest_project_design(
    db: AsyncSession,
    user_id: str,
    project_id: str,
) -> tuple[Design, DesignVersion | None]:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    design_result = await db.execute(
        select(Design)
        .where(Design.project_id == project_id, Design.user_id == user_id)
        .order_by(desc(Design.updated_at))
        .limit(1)
    )
    design = design_result.scalar_one_or_none()
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")

    version_result = await db.execute(
        select(DesignVersion)
        .where(DesignVersion.design_id == design.id)
        .order_by(desc(DesignVersion.version_number))
        .limit(1)
    )
    return design, version_result.scalar_one_or_none()


async def update_design_layout(
    db: AsyncSession,
    user_id: str,
    design_id: str,
    layout_json: dict,
) -> tuple[Design, DesignVersion]:
    result = await db.execute(select(Design).where(Design.id == design_id))
    design = result.scalar_one_or_none()
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    max_version_result = await db.execute(
        select(func.max(DesignVersion.version_number)).where(
            DesignVersion.design_id == design.id
        )
    )
    next_version = (max_version_result.scalar_one_or_none() or 0) + 1
    design.layout_json = layout_json

    version = DesignVersion(
        design_id=design.id,
        project_id=design.project_id,
        user_id=user_id,
        version_number=next_version,
        layout_json=layout_json,
        prompt_used=layout_json.get("metadata", {}).get("prompt"),
    )
    db.add(version)
    await db.commit()
    await db.refresh(design)
    await db.refresh(version)
    return design, version
