"""MVP defaults + room sizing table (workflow Step 0.3, Risk #3).

This table is the layout engine's ground truth: the subdivision engine sizes
cells from ``preferred_area_m2`` and the hard validator rejects any room below
its minima. Values are conservative Indian-residential norms in METERS.

Lives here (not in settings.py) deliberately: settings.py is env-driven runtime
configuration; these are product constants that tests and the engine import
without touching the environment. Documented deviation from the workflow's
single-config.py layout.
"""
from dataclasses import dataclass

from app.schemas.requirements import Facing, RoomType

DEFAULT_PLOT_WIDTH_M = 9.0
DEFAULT_PLOT_DEPTH_M = 12.0
DEFAULT_FACING = Facing.east
UNITS = "meters"

WALL_THICKNESS_M = 0.115
DOOR_WIDTH_M = 0.9
WALL_HEIGHT_M = 3.0
MAX_ROOMS_PER_LAYOUT = 30
MAX_ROOM_ASPECT_RATIO = 2.5
SLIVER_MERGE_UNDER_M = 0.5

INVALID_QUALITY_SCORE_CAP = 49


@dataclass(frozen=True)
class RoomSizing:
    min_w: float
    min_d: float
    preferred_area_m2: float


ROOM_SIZING: dict[RoomType, RoomSizing] = {
    RoomType.bedroom:        RoomSizing(3.0, 3.0, 12.0),
    RoomType.master_bedroom: RoomSizing(3.3, 3.3, 15.0),
    RoomType.bathroom:       RoomSizing(1.5, 2.1, 4.0),
    RoomType.kitchen:        RoomSizing(2.4, 3.0, 9.0),
    RoomType.living_room:    RoomSizing(3.3, 3.6, 16.0),
    RoomType.dining:         RoomSizing(2.7, 3.0, 10.0),
    RoomType.balcony:        RoomSizing(1.2, 2.4, 4.5),
    RoomType.entry:          RoomSizing(1.2, 1.5, 3.0),
    RoomType.pooja_room:     RoomSizing(1.2, 1.5, 2.5),
    RoomType.study:          RoomSizing(2.4, 2.7, 8.0),
    RoomType.utility:        RoomSizing(1.5, 1.8, 3.5),
    RoomType.parking:        RoomSizing(2.7, 5.0, 14.0),
}
