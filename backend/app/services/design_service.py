from fastapi import HTTPException
from sqlalchemy import select
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
