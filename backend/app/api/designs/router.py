from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.design import GenerateRequest, GenerateResponse, SaveDesignRequest
from app.services.auth_service import get_current_user
from app.services.design_service import (
    get_latest_project_design,
    save_generated_design,
    update_design_layout,
)
from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms, extract_total_floors
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

    await log_activity(db, user_id, "design.generated")
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
    design, version = await update_design_layout(db, user_id, design_id, request.layout)
    await log_activity(db, user_id, "layout.saved")
    layout = {
        **design.layout_json,
        "designId": design.id,
        "designVersionId": version.id,
    }
    return GenerateResponse(**layout)
