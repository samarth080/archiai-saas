"""Hard geometric validator (workflow Step 1.3).

Pure function over a LayoutPlan; no I/O, no engine imports beyond schemas and
Rect math. Used three ways: engine self-check (Phase 1 tests), the
/api/validate editor-sync endpoint (Phases 4/7 — called on every drop, so it
must stay fast), and the reject tier of the scorer (Phase 6).

Violation codes (stable API): overlap, out_of_bounds, below_min_size,
unreachable.

Reachability walks the access graph derived from doors: each door's midpoint
connects every room whose boundary touches that point (interior doors connect
two rooms; the front door touches one and adds no edge). The walk starts from
the entry room, or the first room if no entry exists (hand-built plans).
"""
from app.config.mvp_defaults import ROOM_SIZING
from app.schemas.layout_plan import Door, LayoutPlan, PlanRoom, Wall
from app.schemas.quality_report import Violation
from app.schemas.requirements import RoomType
from app.services.layout_engine.geometry import EPS, Rect

_TOUCH_EPS = 0.05  # door-midpoint to room-boundary tolerance (5 cm)


def _rect(room: PlanRoom) -> Rect:
    return Rect(room.x, room.y, room.w, room.h)


def _door_point(door: Door, wall: Wall) -> tuple[float, float]:
    """Midpoint of the door leaf along its host wall."""
    length = abs(wall.x2 - wall.x1) + abs(wall.y2 - wall.y1)
    at = min(door.offset + door.width / 2, length)
    if abs(wall.x2 - wall.x1) <= EPS:  # vertical wall
        y = min(wall.y1, wall.y2) + at
        return wall.x1, y
    x = min(wall.x1, wall.x2) + at
    return x, wall.y1


def _touches(room: PlanRoom, x: float, y: float) -> bool:
    r = _rect(room)
    on_vertical = (abs(x - r.x) <= _TOUCH_EPS or abs(x - r.x2) <= _TOUCH_EPS) and (
        r.y - _TOUCH_EPS <= y <= r.y2 + _TOUCH_EPS
    )
    on_horizontal = (abs(y - r.y) <= _TOUCH_EPS or abs(y - r.y2) <= _TOUCH_EPS) and (
        r.x - _TOUCH_EPS <= x <= r.x2 + _TOUCH_EPS
    )
    return on_vertical or on_horizontal


def validate(plan: LayoutPlan) -> list[Violation]:
    violations: list[Violation] = []
    rooms = plan.rooms
    if not rooms:
        return violations

    plot = Rect(0.0, 0.0, plan.plot.width_m, plan.plot.depth_m)

    # (a) pairwise overlap, epsilon-aware
    for i, a in enumerate(rooms):
        for b in rooms[i + 1:]:
            if _rect(a).overlaps(_rect(b)):
                violations.append(Violation(
                    code="overlap",
                    room_ids=[a.id, b.id],
                    message=f"{a.label} overlaps {b.label}",
                ))

    # (b) inside the plot
    for room in rooms:
        if not plot.contains(_rect(room)):
            violations.append(Violation(
                code="out_of_bounds",
                room_ids=[room.id],
                message=f"{room.label} extends outside the plot",
            ))

    # (c) minimum sizes from the sizing table (orientation-tolerant)
    for room in rooms:
        sizing = ROOM_SIZING[room.type]
        fits = (room.w >= sizing.min_w - EPS and room.h >= sizing.min_d - EPS) or (
            room.w >= sizing.min_d - EPS and room.h >= sizing.min_w - EPS
        )
        if not fits:
            violations.append(Violation(
                code="below_min_size",
                room_ids=[room.id],
                message=(
                    f"{room.label} is {room.w:.1f}x{room.h:.1f} m, below its minimum "
                    f"{sizing.min_w:.1f}x{sizing.min_d:.1f} m"
                ),
            ))

    # (d) every room reachable through doors
    walls_by_id = {w.id: w for w in plan.walls}
    adjacency: dict[str, set[str]] = {room.id: set() for room in rooms}
    for door in plan.doors:
        wall = walls_by_id.get(door.wall_ref)
        if wall is None:
            continue
        x, y = _door_point(door, wall)
        touching = [room.id for room in rooms if _touches(room, x, y)]
        for a in touching:
            for b in touching:
                if a != b:
                    adjacency[a].add(b)

    start = next((r.id for r in rooms if r.type == RoomType.entry), rooms[0].id)
    seen = {start}
    stack = [start]
    while stack:
        for neighbour in adjacency[stack.pop()]:
            if neighbour not in seen:
                seen.add(neighbour)
                stack.append(neighbour)
    for room in rooms:
        if room.id not in seen:
            violations.append(Violation(
                code="unreachable",
                room_ids=[room.id],
                message=f"{room.label} cannot be reached through any door",
            ))

    return violations
