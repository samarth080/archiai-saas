"""LayoutPlan — the locked geometric contract of the MVP pipeline.

COORDINATE CONVENTION (stated here once; never restate it differently anywhere):
    Units are METERS, floats. Origin is the plot's NORTH-WEST corner.
    +x runs EAST, +y runs SOUTH. Plans are north-up.

Rooms are axis-aligned rectangles (x, y = their NW corner). ``rotation`` is
constrained to {0, 90, 180, 270}: the whole geometry stack (overlap tests,
subdivision, IFC/DXF export) is axis-aligned, and a 90° rotation is a w/h swap —
free angles are explicitly out of MVP scope (workflow Step 7.2).

Walls are deduplicated segments (one wall per shared edge, never two overlapping
ones). Doors reference their host wall by id — a door cannot float.

Relationship to the legacy canvas JSON (archiai-saas in-place rework): this is
the new canonical contract for the MVP pipeline; converters map LayoutPlan.rooms
to the existing canvas objects (center-based x/z) so the current 3D editor keeps
working. Walls/doors are DERIVED artifacts — regenerated deterministically from
rooms after every edit, never hand-maintained state.

Rooms are rectangles UNLESS ``vertices`` is set (workflow Phase 8, polygon
boundary engine), in which case ``x/y/w/h`` is the bounding box only and
``vertices`` is the actual straight-edge outline. Likewise ``PlanPlot.boundary``
is None for a plain rectangular plot; when set, ``width_m``/``depth_m`` are the
boundary's bounding box. Curves are out of scope — a vertex list cannot encode
one, so there is nothing further to validate for that constraint.
"""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.requirements import Facing, RoomType, Vertex, _reject_string_number

Meters = Annotated[float, Field(gt=0, lt=200)]
Coord = Annotated[float, Field(ge=-200, le=200)]


class PlanPlot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width_m: Meters
    depth_m: Meters
    facing: Facing = Facing.east
    boundary: list[Vertex] | None = None


class PlanRoom(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: RoomType
    label: str
    x: Coord
    y: Coord
    w: Meters
    h: Meters
    rotation: Literal[0, 90, 180, 270] = 0
    vertices: list[Vertex] | None = None

    @field_validator("x", "y", "w", "h", mode="before")
    @classmethod
    def _no_string_dims(cls, value: object) -> object:
        return _reject_string_number(value)

    @model_validator(mode="after")
    def _no_rotation_with_vertices(self) -> "PlanRoom":
        if self.vertices is not None and self.rotation != 0:
            raise ValueError("rotation must be 0 for a polygon room (vertices set)")
        return self


class Wall(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    x1: Coord
    y1: Coord
    x2: Coord
    y2: Coord
    thickness: float = Field(default=0.115, gt=0, lt=1)


class Door(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    wall_ref: str  # Wall.id hosting this door — doors never float
    offset: float = Field(ge=0)  # meters from the wall's (x1, y1) end
    width: float = Field(default=0.9, gt=0, lt=3)


class LayoutPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plot: PlanPlot
    rooms: list[PlanRoom] = Field(default_factory=list)
    walls: list[Wall] = Field(default_factory=list)
    doors: list[Door] = Field(default_factory=list)
