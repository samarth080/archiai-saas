from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)


class RoomPosition(BaseModel):
    x: float
    y: float
    z: float


class RoomSize(BaseModel):
    w: float
    h: float
    d: float


class RoomResponse(BaseModel):
    id: str
    label: str
    position: RoomPosition
    size: RoomSize
    color: str


class GenerateMetadata(BaseModel):
    prompt: str
    building_type: str
    room_count: int


class GenerateResponse(BaseModel):
    version: str
    metadata: GenerateMetadata
    rooms: list[RoomResponse]
