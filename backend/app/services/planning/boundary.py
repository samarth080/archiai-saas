"""Footprint + oriented boundary model (Phase 4 Stage 2).

Pure geometry, no I/O and no dependency on layout_service (kept acyclic — the
few footprint-width constants below deliberately mirror layout_service's values
rather than importing them). The key export is `split_contact`, the deterministic
rule that tells the slicing tree which footprint edges each child of a guillotine
cut inherits — this is what makes `requires_external_wall` satisfiable by
construction (Phase 4 §4.0 fact 3).

Convention (matches the tiler): footprint anchored at (0,0); z=0 is the front
(entry) edge = South, z=d is the back = North, x=0 is West (left), x=w is East.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

# Mirror of layout_service's footprint-width bounds (duplicated to avoid a
# planning<->layout_service import cycle; keep in sync).
_MIN_BUILDING_WIDTH = 7.0
_MAX_BUILDING_WIDTH = 22.0
_PLOT_WIDTH_MIN = 4.0
_PLOT_WIDTH_MAX = 40.0

# Circulation overhead added to the raw program area when sizing the footprint.
CIRCULATION_RATIO = {
    "residential": 0.12,
    "commercial": 0.18,
    "healthcare": 0.22,
}

_NORTH, _EAST, _SOUTH, _WEST = "N", "E", "S", "W"
ALL_EDGES = frozenset({_NORTH, _EAST, _SOUTH, _WEST})

# DesignParams orientation (road/entry-facing side) -> which footprint edge is
# the front (entry) edge.
_ORIENTATION_FRONT = {"S": _SOUTH, "N": _NORTH, "E": _EAST, "W": _WEST}


@dataclass(frozen=True)
class Rect:
    x: float
    z: float
    w: float
    d: float

    @property
    def area(self) -> float:
        return self.w * self.d

    @property
    def cx(self) -> float:
        return self.x + self.w / 2

    @property
    def cz(self) -> float:
        return self.z + self.d / 2


@dataclass(frozen=True)
class Boundary:
    footprint: Rect
    front: str = _SOUTH
    front_door_center: tuple[float, float] = (0.0, 0.0)

    def edge_length(self, edge: str) -> float:
        return self.footprint.w if edge in (_NORTH, _SOUTH) else self.footprint.d


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def compute_footprint(
    total_area: float,
    *,
    circulation_ratio: float = 0.12,
    plot_width_m: float | None = None,
) -> Rect:
    """Rectangular footprint sized from the program area — width mirrors the
    tiler (sqrt(area*1.6) clamped, or an explicit plot width), depth carries the
    area budget including circulation overhead."""
    if total_area <= 0:
        return Rect(0.0, 0.0, 0.0, 0.0)
    budget = total_area * (1.0 + circulation_ratio)
    if plot_width_m is not None:
        width = _clamp(round(plot_width_m, 1), _PLOT_WIDTH_MIN, _PLOT_WIDTH_MAX)
    else:
        width = _clamp(round(sqrt(total_area * 1.6), 1), _MIN_BUILDING_WIDTH, _MAX_BUILDING_WIDTH)
    depth = round(budget / width, 2)
    return Rect(0.0, 0.0, width, depth)


def build_boundary(footprint: Rect, orientation: str | None = None) -> Boundary:
    front = _ORIENTATION_FRONT.get((orientation or "S").upper(), _SOUTH)
    # Front-door segment: centred on the front edge by default.
    if front in (_SOUTH, _NORTH):
        door = (footprint.cx, footprint.z if front == _SOUTH else footprint.z + footprint.d)
    else:
        door = (footprint.x if front == _WEST else footprint.x + footprint.w, footprint.cz)
    return Boundary(footprint=footprint, front=front, front_door_center=door)


def split_contact(contact: frozenset[str], direction: str) -> tuple[frozenset[str], frozenset[str]]:
    """Split a rectangle's boundary contact across a guillotine cut.

    A *vertical* cut (constant-x line) yields left | right children: both keep
    the parent's N/S contact, the left keeps W, the right keeps E. A *horizontal*
    cut (constant-z line) yields front | back children: both keep E/W, the front
    (low z) keeps S, the back keeps N. Returns (child_a_contact, child_b_contact)
    where a = left/front, b = right/back — matching the guillotine ordering.
    """
    if direction == "vertical":
        shared = contact & {_NORTH, _SOUTH}
        left = shared | (contact & {_WEST})
        right = shared | (contact & {_EAST})
        return left, right
    shared = contact & {_EAST, _WEST}
    front = shared | (contact & {_SOUTH})
    back = shared | (contact & {_NORTH})
    return front, back
