from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.project import PublicProjectSummary, PublicSharedProjectOut
from app.services.export_share_service import get_shared_project_by_token

router = APIRouter(prefix="/api/share", tags=["shares"])


@router.get("/{token}", response_model=PublicSharedProjectOut)
async def get_shared_project(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> PublicSharedProjectOut:
    _, project, design, version = await get_shared_project_by_token(db, token)
    layout = None
    if design is not None:
        layout = {
            **design.layout_json,
            "designId": design.id,
            "designVersionId": version.id if version is not None else None,
        }
    return PublicSharedProjectOut(
        project=PublicProjectSummary(
            id=project.id,
            title=project.title,
            description=project.description,
        ),
        layout=layout,
    )
