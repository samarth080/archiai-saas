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


class AdjacencyPref(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_a: RoomType
    room_b: RoomType
    strength: Literal["must", "should"]


class AvoidPair(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room_a: RoomType
    room_b: RoomType


class PlotSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    width_m: Meters | None = None
    depth_m: Meters | None = None

    @field_validator("width_m", "depth_m", mode="before")
    @classmethod
    def _no_string_dims(cls, value: object) -> object:
        return _reject_string_number(value)


class RequirementsSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    building_type: BuildingType = BuildingType.house
    floors: StrictInt = Field(default=1, ge=1, le=5)
    rooms: list[RoomRequest] = Field(default_factory=list)
    adjacency: list[AdjacencyPref] = Field(default_factory=list)
    avoid_adjacency: list[AvoidPair] = Field(default_factory=list)
    plot: PlotSpec = Field(default_factory=PlotSpec)
    facing: Facing | None = None
    # Field names / question topics the prompt genuinely did not state.
    missing_info: list[str] = Field(default_factory=list)
