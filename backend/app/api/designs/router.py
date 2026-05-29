from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.models.design import Design
from app.models.design_version import DesignVersion
from app.schemas.design import (
    GenerateRequest,
    GenerateResponse,
    RefineRequest,
    RefineResponse,
    SaveDesignRequest,
)
from app.services.auth_service import get_current_user
from app.services.design_service import (
    get_latest_project_design,
    save_generated_design,
    update_design_layout,
)
from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms, extract_total_floors
from app.services.refinement_service import apply_refinement, parse_refinement
from app.utils.activity import log_activity

router = APIRouter(prefix="/api/design", tags=["design"])
_bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return str(user.id)


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    room_specs = extract_rooms(request.prompt)
    if not room_specs:
        raise HTTPException(
            status_code=422,
            detail="No rooms detected. Try: '2 bedroom apartment with kitchen'",
        )
    building_type = detect_building_type(request.prompt)
    total_floors = extract_total_floors(request.prompt)
    layout = generate_layout(
        room_specs,
        prompt=request.prompt,
        building_type=building_type,
        total_floors=total_floors,
    )
    if request.project_id:
        design, version = await save_generated_design(
            db,
            user_id=user_id,
            project_id=request.project_id,
            layout_json=layout,
            prompt=request.prompt,
        )
        layout["designId"] = design.id
        layout["designVersionId"] = version.id

    await log_activity(
        db, user_id, "design.generated", project_id=request.project_id
    )
    return GenerateResponse(**layout)


@router.get("/project/{project_id}/latest", response_model=GenerateResponse)
async def latest_for_project(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    design, version = await get_latest_project_design(db, user_id, project_id)
    layout = {
        **design.layout_json,
        "designId": design.id,
        "designVersionId": version.id if version else None,
    }
    return GenerateResponse(**layout)


@router.put("/{design_id}", response_model=GenerateResponse)
async def save_design(
    design_id: str,
    request: SaveDesignRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    design, version = await update_design_layout(
        db,
        user_id,
        design_id,
        request.layout,
        version_name=request.version_name,
        change_summary=request.change_summary,
        thumbnail_url=request.thumbnail_url,
    )
    await log_activity(db, user_id, "layout.saved", project_id=design.project_id)
    layout = {
        **design.layout_json,
        "designId": design.id,
        "designVersionId": version.id,
    }
    return GenerateResponse(**layout)


@router.post("/refine", response_model=RefineResponse)
async def refine(
    request: RefineRequest,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> RefineResponse:
    design = await db.get(Design, request.design_id)
    if design is None:
        raise HTTPException(status_code=404, detail="Design not found")
    if design.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    ops = parse_refinement(request.prompt)
    if not ops:
        raise HTTPException(
            status_code=422,
            detail=(
                "Couldn't understand the refinement. "
                "Try: 'add a bedroom', 'remove the office', 'make the kitchen bigger'."
            ),
        )

    new_layout, summary = apply_refinement(design.layout_json, ops)
    if not summary:
        raise HTTPException(
            status_code=422, detail="No matching rooms found for that change."
        )

    design.layout_json = new_layout
    design.updated_at = datetime.now(timezone.utc)

    max_version = await db.scalar(
        select(func.max(DesignVersion.version_number)).where(
            DesignVersion.design_id == design.id
        )
    )
    next_version = (max_version or 0) + 1

    version = DesignVersion(
        design_id=design.id,
        project_id=design.project_id,
        user_id=user_id,
        version_number=next_version,
        version_name=f"Refinement v{next_version}",
        version_type="refined",
        change_summary=summary,
        layout_json=new_layout,
        prompt_used=request.prompt,
    )
    db.add(version)
    await db.commit()
    await db.refresh(design)
    await db.refresh(version)

    await log_activity(db, user_id, "design.refined", project_id=design.project_id)

    return RefineResponse(
        **new_layout,
        designId=design.id,
        designVersionId=version.id,
        refinementSummary=summary,
    )


@router.get("/version/{version_id}", response_model=GenerateResponse)
async def fetch_version(
    version_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    version = await db.get(DesignVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    design = await db.get(Design, version.design_id)
    if design is None or design.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    layout = {
        k: v
        for k, v in version.layout_json.items()
        if k not in ("designId", "designVersionId")
    }
    return GenerateResponse(
        **layout,
        designId=design.id,
        designVersionId=version.id,
    )
