"""Hard geometric validator (workflow Step 1.3).

Pure function over a LayoutPlan; no I/O, no engine imports beyond schemas and
Rect math. Used three ways: engine self-check (Phase 1 tests), the
/api/validate editor-sync endpoint (Phases 4/7 — called on every drop, so it
must stay fast), and the reject tier of the scorer (Phase 6).

Violation codes (stable API): overlap, out_of_bounds, below_min_size,
unreachable, missing_requested_room.

Reachability walks the access graph derived from doors: each door's midpoint
connects every room whose boundary touches that point (interior doors connect
two rooms; the front door touches one and adds no edge). The walk starts from
the entry room, or the first room if no entry exists (hand-built plans).

``requirements`` is optional (Packet 7.1 — prompt-to-program truth gate): the
fast per-drop editor endpoint has no RequirementsSpec to compare against and
must keep validating geometry only, so passing it stays opt-in and
backward-compatible. When supplied (the scorer always has one), a requested
room type/count entirely missing from the plan is a hard violation, not a
soft-scored warning — the engine already guarantees exact requested counts,
so a shortfall here means the source requirements or a later edit dropped a
requested room, and quality must not call that layout satisfactory.
"""
from app.schemas.layout_plan import Door, LayoutPlan, PlanRoom, Wall
from app.schemas.quality_report import Violation
from app.schemas.requirements import RequirementsSpec, RoomType
from app.services import catalog
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


def _missing_requested_rooms(
    rooms: list[PlanRoom], requirements: RequirementsSpec
) -> list[Violation]:
    generated_counts: dict[RoomType, int] = {}
    for room in rooms:
        generated_counts[room.type] = generated_counts.get(room.type, 0) + 1

    requested_counts: dict[RoomType, int] = {}
    for requested in requirements.rooms:
        requested_counts[requested.type] = (
            requested_counts.get(requested.type, 0) + requested.count
        )

    violations: list[Violation] = []
    for room_type in sorted(requested_counts, key=lambda t: t.value):
        shortfall = requested_counts[room_type] - generated_counts.get(room_type, 0)
        if shortfall > 0:
            label = room_type.value.replace("_", " ")
            violations.append(Violation(
                code="missing_requested_room",
                room_ids=[],
                message=(
                    f"Requested {requested_counts[room_type]} {label}(s) but the "
                    f"layout only has {generated_counts.get(room_type, 0)}"
                ),
            ))
    return violations


def validate(
    plan: LayoutPlan, requirements: RequirementsSpec | None = None
) -> list[Violation]:
    violations: list[Violation] = []
    rooms = plan.rooms
    if requirements is not None:
        violations.extend(_missing_requested_rooms(rooms, requirements))
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

    # (c) minimum sizes from the sizing table (orientation-tolerant). Lenient
    # catalog lookup — never raises — so a non-residential room type still
    # gets a real minimum instead of a KeyError; see min_dimensions' own
    # docstring for why this stays permissive here.
    for room in rooms:
        min_w, min_d = catalog.min_dimensions(room.type)
        fits = (room.w >= min_w - EPS and room.h >= min_d - EPS) or (
            room.w >= min_d - EPS and room.h >= min_w - EPS
        )
        if not fits:
            violations.append(Violation(
                code="below_min_size",
                room_ids=[room.id],
                message=(
                    f"{room.label} is {room.w:.1f}x{room.h:.1f} m, below its minimum "
                    f"{min_w:.1f}x{min_d:.1f} m"
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
