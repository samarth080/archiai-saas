from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DesignParams(BaseModel):
    """
    Explicit parametric overrides for layout generation, alongside the prompt.
    All fields are optional; when omitted the engine falls back to its existing
    prompt-inferred behaviour. plot_width_m, floors, orientation, and vastu all
    affect generated geometry; plot_depth_m is recorded but not yet applied — it
    needs the BSP partitioner (Phase 2) to constrain depth without distorting
    room proportions the way a naive clamp would.
    """

    plot_width_m: float | None = Field(default=None, alias="plotWidthM", gt=0)
    plot_depth_m: float | None = Field(default=None, alias="plotDepthM", gt=0)
    floors: int | None = Field(default=None, ge=1, le=6)
    orientation: str | None = None
    """Road-facing / entry side: one of N, S, E, W. Defaults to S (front wall) when omitted."""
    vastu: bool | None = None

    model_config = {"populate_by_name": True}


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    project_id: str | None = Field(default=None, alias="projectId")
    design_params: DesignParams | None = Field(default=None, alias="designParams")

    model_config = {"populate_by_name": True}


class SaveDesignRequest(BaseModel):
    layout: dict[str, Any]
    version_name: str | None = Field(default=None, alias="versionName")
    change_summary: str | None = Field(default=None, alias="changeSummary")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")

    model_config = {"populate_by_name": True}


class DesignDraftSaveRequest(BaseModel):
    layout: dict[str, Any]


class RefineRequest(BaseModel):
    design_id: str = Field(..., alias="designId")
    prompt: str = Field(..., min_length=3)

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
    zone: str | None = None
    position: RoomPosition
    size: RoomSize
    rotation: RoomRotation | None = None
    color: str


class GenerateMetadata(BaseModel):
    prompt: str | None = None
    building_type: str | None = None
    buildingType: str | None = None
    style: str | None = None
    room_count: int | None = None
    totalFloors: int | None = None
    totalRooms: int | None = None
    totalAreaSqm: float | None = None
    requestedAreaSqm: float | None = None
    patternDataUsed: bool | None = None
    patternDataSource: str | None = None
    zonesDetected: list[str] | None = None
    template: str | None = None
    templateStrategy: str | None = None
    designParams: dict[str, Any] | None = None
    placementEngine: str | None = None
    candidateCount: int | None = None


class BuildingResponse(BaseModel):
    floorHeight: float


class FloorFootprint(BaseModel):
    x: float
    z: float
    w: float
    d: float


class FloorResponse(BaseModel):
    id: str
    name: str
    level: int
    elevation: float
    footprint: FloorFootprint | None = None
    rooms: list[RoomResponse]


class GenerationInsights(BaseModel):
    score: int
    reasons: list[str]
    warnings: list[str]
    appliedRules: list[str]


class GenerateResponse(BaseModel):
    version: str
    designId: str | None = None
    designVersionId: str | None = None
    metadata: GenerateMetadata
    building: BuildingResponse | None = None
    floors: list[FloorResponse] | None = None
    rooms: list[RoomResponse]
    insights: GenerationInsights | None = None


class RefineResponse(GenerateResponse):
    refinementSummary: str


class DesignDraftResponse(GenerateResponse):
    id: str
    projectId: str
    versionNumber: int
    versionType: str
    changeSummary: str | None = None
    createdAt: datetime
    metadata: dict[str, Any]
