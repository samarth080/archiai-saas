from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.design import GenerateRequest, GenerateResponse
from app.services.auth_service import get_current_user
from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms

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
    _user_id: str = Depends(_current_user_id),
) -> GenerateResponse:
    room_specs = extract_rooms(request.prompt)
    if not room_specs:
        raise HTTPException(
            status_code=422,
            detail="No rooms detected. Try: '2 bedroom apartment with kitchen'",
        )
    building_type = detect_building_type(request.prompt)
    layout = generate_layout(room_specs, prompt=request.prompt, building_type=building_type)
    return GenerateResponse(**layout)
