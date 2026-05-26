from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas.design import GenerateRequest, GenerateResponse
from app.services.layout_service import generate_layout
from app.services.prompt_service import detect_building_type, extract_rooms
from app.utils.jwt import decode_access_token

router = APIRouter(prefix="/api/design", tags=["design"])
_bearer = HTTPBearer(auto_error=False)


async def _require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    request: GenerateRequest,
    _user_id: str = Depends(_require_auth),
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
