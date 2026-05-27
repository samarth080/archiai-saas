from typing import Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    project_id: str | None = Field(default=None, alias="projectId")

    model_config = {"populate_by_name": True}


class SaveDesignRequest(BaseModel):
    layout: dict[str, Any]
    version_name: str | None = Field(default=None, alias="versionName")
    change_summary: str | None = Field(default=None, alias="changeSummary")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")

    model_config = {"populate_by_name": True}


class RoomPosition(BaseModel):
    x: float
    y: float
    z: float


class RoomSize(BaseModel):
    w: float
    h: float
    d: float


class RoomRotation(BaseModel):
    x: float
    y: float
    z: float


class RoomResponse(BaseModel):
    id: str
    label: str
    roomType: str | None = None
    objectType: str | None = None
    floorId: str | None = None
    floorLevel: int | None = None
    position: RoomPosition
    size: RoomSize
    rotation: RoomRotation | None = None
    color: str


class GenerateMetadata(BaseModel):
    prompt: str
    building_type: str
    buildingType: str | None = None
    style: str | None = None
    room_count: int
    totalFloors: int | None = None
    totalRooms: int | None = None
    totalAreaSqm: float | None = None


class BuildingResponse(BaseModel):
    floorHeight: float


class FloorResponse(BaseModel):
    id: str
    name: str
    level: int
    elevation: float
    rooms: list[RoomResponse]


class GenerateResponse(BaseModel):
    version: str
    designId: str | None = None
    designVersionId: str | None = None
    metadata: GenerateMetadata
    building: BuildingResponse | None = None
    floors: list[FloorResponse] | None = None
    rooms: list[RoomResponse]
