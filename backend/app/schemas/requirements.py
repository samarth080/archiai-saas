"""RequirementsSpec — the locked contract between LLM extraction and everything else.

This is the single output shape of the extraction service (Phase 2) and the single
input shape of the MVP layout engine (Phase 1). It is deliberately strict:

- ``RoomType`` is a CLOSED enum. The extraction normalizer maps synonyms
  (hall→living_room, toilet/washroom→bathroom, drawing room→living_room) BEFORE
  validation; anything unmappable is rejected, never invented.
- **master_bedroom counting rule** (locked here, relied on by extraction, the
  engine, and the "AI understood" panel): "N BHK" means N bedrooms TOTAL. If a
  master bedroom is mentioned, it is ONE OF the N (1 master + N-1 bedroom), never
  additive. "3BHK with master bedroom" = 1 master_bedroom + 2 bedroom.
- The extractor must never invent plot size or facing: absent means None here,
  and the field name goes into ``missing_info``.
- Wrong-typed values (count "three", width "3.5" as a string) must raise
  ValidationError — the Risk #4 failure mode is caught at this boundary, not
  downstream.

Changing this file is a mini-migration, not a casual edit (workflow Step 0.3).
"""
from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class BuildingType(str, Enum):
    house = "house"
    apartment = "apartment"
    villa = "villa"
    duplex = "duplex"
    clinic = "clinic"
    office = "office"
    other = "other"


class RoomType(str, Enum):
    """Closed vocabulary. The engine sizing table, Vastu rules, and normalizer
    glossary are all keyed by exactly these twelve values."""

    bedroom = "bedroom"
    master_bedroom = "master_bedroom"
    bathroom = "bathroom"
    kitchen = "kitchen"
    living_room = "living_room"
    dining = "dining"
    balcony = "balcony"
    entry = "entry"
    pooja_room = "pooja_room"
    study = "study"
    utility = "utility"
    parking = "parking"


class Facing(str, Enum):
    north = "north"
    south = "south"
    east = "east"
    west = "west"


def _reject_string_number(value: object) -> object:
    """Dimensions must arrive as numbers, not numeric strings — the schema is the
    type gate for LLM output (workflow Risk #4)."""
    if isinstance(value, str):
        raise ValueError("must be a number, not a string")
    return value


Meters = Annotated[float, Field(gt=0, lt=100)]


class RoomRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: RoomType
    # StrictInt: rejects "three", 3.0, true. The normalizer converts words to
    # ints before validation; >10 of one type is flagged as a conflict there.
    count: StrictInt = Field(ge=1, le=50)


class SpaceRequest(BaseModel):
    """Phase 1 (engine generalization) superset of RoomRequest: a free-string
    `space_type` validated against `services.catalog.SpaceCatalog` at the
    service boundary rather than the closed `RoomType` enum, so the contract
    can eventually express non-residential programs `RoomType` cannot. Added
    additively alongside `rooms` (workflow Phase 1.2 migration order item 1)
    — `rooms` keeps working exactly as before; nothing existing reads
    `spaces` yet."""

    model_config = ConfigDict(extra="forbid")

    space_type: str = Field(min_length=1, max_length=64)
    count: StrictInt = Field(ge=1, le=50)
    size_hint: Literal["small", "medium", "large", "xlarge"] | None = None
    # Explicit user override beats any hint or catalog default.
    area_m2: float | None = Field(default=None, gt=1, lt=2000)


class AdjacencyPref(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_a: RoomType
    room_b: RoomType
    strength: Literal["must", "should"]


class AvoidPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_a: RoomType
    room_b: RoomType


class Vertex(BaseModel):
    """A single (x, y) boundary/room-outline point, same meters/NW-origin
    convention as LayoutPlan (workflow Phase 8, polygon boundary engine).
    Defined here rather than layout_plan.py: that module already imports
    from this one (Facing, RoomType), so putting Vertex here — where PlotSpec
    needs it too — avoids a circular import."""

    model_config = ConfigDict(extra="forbid")

    x: Annotated[float, Field(ge=-200, le=200)]
    y: Annotated[float, Field(ge=-200, le=200)]


class PlotSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width_m: Meters | None = None
    depth_m: Meters | None = None
    # Straight-edge polygon footprint override (workflow Phase 8). When set,
    # the engine subdivides this boundary directly instead of a width_m x
    # depth_m rectangle; width_m/depth_m (if also present) are ignored by the
    # engine but may still be used for display/estimation upstream.
    boundary: list[Vertex] | None = None

    @field_validator("width_m", "depth_m", mode="before")
    @classmethod
    def _no_string_dims(cls, value: object) -> object:
        return _reject_string_number(value)


class RequirementsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    building_type: BuildingType = BuildingType.house
    floors: StrictInt = Field(default=1, ge=1, le=5)
    rooms: list[RoomRequest] = Field(default_factory=list)
    # Superset of `rooms` (Phase 1.2) — free-string SpaceRequest entries.
    # Nothing populates or reads this yet; it exists so the migration can
    # proceed one call site at a time instead of a single breaking cutover.
    spaces: list[SpaceRequest] = Field(default_factory=list)
    adjacency: list[AdjacencyPref] = Field(default_factory=list)
    avoid_adjacency: list[AvoidPair] = Field(default_factory=list)
    plot: PlotSpec = Field(default_factory=PlotSpec)
    facing: Facing | None = None
    # Explicit archetype override (workflow Phase 3.2) — None lets the
    # engine's graph-shape selector choose; closed to the archetypes the
    # engine actually implements, same "reject, never invent" posture as
    # every other enum in this file.
    layout_style: Literal[
        "zoned_bands", "double_loaded_corridor", "hub_and_spoke", "open_core"
    ] | None = None
    # Field names / question topics the prompt genuinely did not state.
    missing_info: list[str] = Field(default_factory=list)
