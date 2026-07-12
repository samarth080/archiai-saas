"""RequirementsSpec -> LayoutPlan orchestrator (workflow Step 1.2).

Pipeline: expand counts (auto-entry, master rule is upstream in the spec) ->
zone public/private -> split the plot into a facing-side public band and a
private band -> recursive subdivision per band -> leaf min-size check (a room
that would fall below its sizing-table minimum raises DoesNotFitError — the
structured "plot too small" the API turns into a clarification) -> emit
deduplicated walls (one wall per shared edge) -> place doors (must-adjacency
first, then a BFS spanning tree from the circulation room so the access graph
is connected by construction, plus the front door on the entry's facing wall).

v0 limitations (documented, deliberate): single storey — `floors > 1` places
every room on one plot (the duplex case is an extraction/clarification concern,
not an engine one, until Section 17 work); rooms are emitted with rotation=0.
"""
from app.config.mvp_defaults import (
    DEFAULT_FACING,
    DEFAULT_PLOT_DEPTH_M,
    DEFAULT_PLOT_WIDTH_M,
    DOOR_WIDTH_M,
    MAX_ROOMS_PER_LAYOUT,
    PRIVATE_ROOM_TYPES,
    PUBLIC_ROOM_TYPES,
    ROOM_SIZING,
    WALL_THICKNESS_M,
)
from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.requirements import Facing, RequirementsSpec, RoomType
from app.services.layout_engine.geometry import EPS, Rect, Segment
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError, subdivide

_MIN_DOOR_EDGE = DOOR_WIDTH_M + 0.1     # a door needs this much shared wall
_NARROW_DOOR_WIDTH = 0.7                # connectivity fallback on tight edges
_NARROW_DOOR_EDGE = _NARROW_DOOR_WIDTH + 0.1

# Placement order inside each band: entry leads (facing bias pulls it to the
# facing edge), circulation-heavy rooms early, service rooms last.
_PUBLIC_ORDER = [
    RoomType.entry, RoomType.living_room, RoomType.dining,
    RoomType.kitchen, RoomType.balcony, RoomType.parking,
]
_PRIVATE_ORDER = [
    RoomType.master_bedroom, RoomType.bathroom, RoomType.bedroom,
    RoomType.study, RoomType.pooja_room, RoomType.utility,
]


class DoesNotFitError(ValueError):
    """Structured 'plot too small' error. Phase 4 maps this to a 422
    clarification ("increase plot size?")."""

    def __init__(self, message: str, *, required_area: float | None = None, plot_area: float | None = None):
        super().__init__(message)
        self.required_area = required_area
        self.plot_area = plot_area


# ── Expansion + zoning ────────────────────────────────────────────────────────


def _label(room_type: RoomType, index: int, count: int) -> str:
    base = room_type.value.replace("_", " ").title()
    return f"{base} {index}" if count > 1 else base


def _expand(spec: RequirementsSpec) -> list[RoomNeed]:
    needs: list[RoomNeed] = []
    counter = 0
    counts = {r.type: r.count for r in spec.rooms}
    if RoomType.entry not in counts:
        counts[RoomType.entry] = 1  # every plan needs a way in
    for room_type, count in counts.items():
        sizing = ROOM_SIZING[room_type]
        for i in range(1, count + 1):
            counter += 1
            needs.append(RoomNeed(
                key=f"r{counter}",
                type=room_type.value,
                label=_label(room_type, i, count),
                preferred_area=sizing.preferred_area_m2,
                min_w=sizing.min_w,
                min_d=sizing.min_d,
            ))
    return needs


def _order_group(group: list[RoomNeed], order: list[RoomType], spec: RequirementsSpec) -> list[RoomNeed]:
    rank = {t.value: i for i, t in enumerate(order)}
    ordered = sorted(group, key=lambda n: (rank.get(n.type, 99), n.key))

    # Soft adjacency as placement order: pull one partner of each `must` pair
    # directly behind the first room of the other type (attached bathroom
    # behind the master bedroom, etc.).
    for pref in spec.adjacency:
        if pref.strength != "must":
            continue
        anchor = next((n for n in ordered if n.type == pref.room_a.value), None)
        partner = next((n for n in ordered if n.type == pref.room_b.value), None)
        if anchor is None or partner is None:
            anchor = next((n for n in ordered if n.type == pref.room_b.value), None)
            partner = next((n for n in ordered if n.type == pref.room_a.value), None)
        if anchor is None or partner is None or anchor is partner:
            continue
        ordered.remove(partner)
        ordered.insert(ordered.index(anchor) + 1, partner)
    return ordered


# ── Bands ─────────────────────────────────────────────────────────────────────


def _bands(plot_w: float, plot_d: float, facing: Facing, public: list[RoomNeed], private: list[RoomNeed]):
    """(band_rect, ordered_group) pairs — public band on the facing side."""
    if not public or not private:
        return [(Rect(0.0, 0.0, plot_w, plot_d), public or private)]

    area_pub = sum(n.preferred_area for n in public)
    area_prv = sum(n.preferred_area for n in private)
    share = area_pub / (area_pub + area_prv)

    if facing in (Facing.east, Facing.west):
        span, other = plot_w, plot_d
    else:
        span, other = plot_d, plot_w
    t = span * share
    floor_pub = max(1.5, sum(n.min_area for n in public) * 1.02 / other)
    floor_prv = max(1.5, sum(n.min_area for n in private) * 1.02 / other)
    if floor_pub + floor_prv > span + EPS:
        raise DoesNotFitError(
            "plot too small to separate public and private zones — increase plot size",
            required_area=sum(n.min_area for n in public + private),
            plot_area=plot_w * plot_d,
        )
    t = min(max(t, floor_pub), span - floor_prv)

    if facing == Facing.east:
        pub, prv = Rect(plot_w - t, 0, t, plot_d), Rect(0, 0, plot_w - t, plot_d)
    elif facing == Facing.west:
        pub, prv = Rect(0, 0, t, plot_d), Rect(t, 0, plot_w - t, plot_d)
    elif facing == Facing.south:
        pub, prv = Rect(0, plot_d - t, plot_w, t), Rect(0, 0, plot_w, plot_d - t)
    else:  # north
        pub, prv = Rect(0, 0, plot_w, t), Rect(0, t, plot_w, plot_d - t)
    return [(pub, public), (prv, private)]


# ── Walls (deduplicated) + doors ─────────────────────────────────────────────


def _round(v: float) -> float:
    return round(v, 3)


def _build_walls(placed: list[tuple[RoomNeed, Rect]], plot_w: float, plot_d: float):
    """One wall per shared edge (never two overlapping ones) + boundary walls.

    Returns (walls, wall_rooms) where wall_rooms maps wall id -> (key_a, key_b)
    with key_b None for boundary walls — the internal adjacency the door placer
    and validator need but the LayoutPlan contract deliberately omits.
    """
    walls: list[Wall] = []
    wall_rooms: dict[str, tuple[str, str | None]] = {}

    def add(seg: Segment, a: str, b: str | None) -> str:
        wall_id = f"w{len(walls) + 1}"
        walls.append(Wall(
            id=wall_id,
            x1=_round(seg.x1), y1=_round(seg.y1),
            x2=_round(seg.x2), y2=_round(seg.y2),
            thickness=WALL_THICKNESS_M,
        ))
        wall_rooms[wall_id] = (a, b)
        return wall_id

    for i, (need_a, rect_a) in enumerate(placed):
        for need_b, rect_b in placed[i + 1:]:
            seg = rect_a.shared_edge(rect_b)
            if seg is not None:
                add(seg, need_a.key, need_b.key)

    for need, rect in placed:  # boundary portions belong to exactly one room
        if rect.x <= EPS:
            add(Segment(0.0, rect.y, 0.0, rect.y2), need.key, None)
        if rect.x2 >= plot_w - EPS:
            add(Segment(plot_w, rect.y, plot_w, rect.y2), need.key, None)
        if rect.y <= EPS:
            add(Segment(rect.x, 0.0, rect.x2, 0.0), need.key, None)
        if rect.y2 >= plot_d - EPS:
            add(Segment(rect.x, plot_d, rect.x2, plot_d), need.key, None)
    return walls, wall_rooms


def _wall_length(w: Wall) -> float:
    return abs(w.x2 - w.x1) + abs(w.y2 - w.y1)


def _circulation_key(placed: list[tuple[RoomNeed, Rect]]) -> str:
    by_type = {n.type: n.key for n, _ in placed}
    if RoomType.living_room.value in by_type:
        return by_type[RoomType.living_room.value]
    if RoomType.entry.value in by_type:
        return by_type[RoomType.entry.value]
    return placed[0][0].key


def _place_doors(
    placed: list[tuple[RoomNeed, Rect]],
    walls: list[Wall],
    wall_rooms: dict[str, tuple[str, str | None]],
    spec: RequirementsSpec,
    facing: Facing,
) -> list[Door]:
    doors: list[Door] = []
    doored_walls: set[str] = set()

    def add_door(wall: Wall, width: float) -> None:
        if wall.id in doored_walls:
            return
        doored_walls.add(wall.id)
        offset = max(0.0, (_wall_length(wall) - width) / 2)
        doors.append(Door(id=f"d{len(doors) + 1}", wall_ref=wall.id, offset=_round(offset), width=width))

    interior = [w for w in walls if wall_rooms[w.id][1] is not None]
    by_pair: dict[frozenset, list[Wall]] = {}
    for wall in interior:
        a, b = wall_rooms[wall.id]
        by_pair.setdefault(frozenset((a, b)), []).append(wall)

    types_by_key = {n.key: n.type for n, _ in placed}

    # 1. `must`-adjacency doors (attached bathroom onto its bedroom, etc.).
    for pref in spec.adjacency:
        if pref.strength != "must":
            continue
        for pair, pair_walls in by_pair.items():
            pair_types = {types_by_key[k] for k in pair}
            if pair_types == {pref.room_a.value, pref.room_b.value} or (
                pref.room_a == pref.room_b and len(pair_types) == 1 and pair_types == {pref.room_a.value}
            ):
                best = max(pair_walls, key=_wall_length)
                if _wall_length(best) >= _MIN_DOOR_EDGE:
                    add_door(best, DOOR_WIDTH_M)
                break

    # 2. BFS spanning tree from the circulation room — connectivity by
    #    construction. Wide doors preferred; narrow fallback keeps a tight
    #    plan reachable rather than failing it.
    circulation = _circulation_key(placed)
    connected = {circulation}
    for door in doors:  # must-doors already made may pre-connect rooms
        a, b = wall_rooms[door.wall_ref]
        if a in connected or (b or "") in connected:
            connected.update({a, b} if b else {a})

    changed = True
    while changed:
        changed = False
        for pair, pair_walls in sorted(by_pair.items(), key=lambda kv: sorted(kv[0])):
            a, b = sorted(pair)
            if (a in connected) == (b in connected):
                continue
            best = max(pair_walls, key=_wall_length)
            if _wall_length(best) >= _MIN_DOOR_EDGE:
                add_door(best, DOOR_WIDTH_M)
            elif _wall_length(best) >= _NARROW_DOOR_EDGE:
                add_door(best, _NARROW_DOOR_WIDTH)
            else:
                continue
            connected.update(pair)
            changed = True

    unreachable = [n.label for n, _ in placed if n.key not in connected]
    if unreachable:
        raise DoesNotFitError(
            f"no door-sized wall reaches: {', '.join(unreachable)} — increase plot size"
        )

    # 3. Front door on the entry's facing-side boundary wall (best effort).
    entry_key = next((n.key for n, _ in placed if n.type == RoomType.entry.value), None)
    if entry_key is not None:
        def on_facing(wall: Wall) -> bool:
            if facing == Facing.east:
                return abs(wall.x1 - wall.x2) <= EPS and wall.x1 > 0
            if facing == Facing.west:
                return abs(wall.x1 - wall.x2) <= EPS and wall.x1 <= EPS
            if facing == Facing.south:
                return abs(wall.y1 - wall.y2) <= EPS and wall.y1 > 0
            return abs(wall.y1 - wall.y2) <= EPS and wall.y1 <= EPS

        boundary = [
            w for w in walls
            if wall_rooms[w.id] == (entry_key, None) and _wall_length(w) >= _MIN_DOOR_EDGE
        ]
        best = next((w for w in boundary if on_facing(w)), None) or (boundary[0] if boundary else None)
        if best is not None:
            add_door(best, DOOR_WIDTH_M)

    return doors


# ── Public entrypoint ─────────────────────────────────────────────────────────


def generate_plan(spec: RequirementsSpec) -> LayoutPlan:
    plot_w = spec.plot.width_m or DEFAULT_PLOT_WIDTH_M
    plot_d = spec.plot.depth_m or DEFAULT_PLOT_DEPTH_M
    facing = spec.facing or DEFAULT_FACING

    needs = _expand(spec)
    if not needs:
        raise DoesNotFitError("no rooms requested")
    if len(needs) > MAX_ROOMS_PER_LAYOUT:
        raise DoesNotFitError(f"more than {MAX_ROOMS_PER_LAYOUT} rooms requested")

    plot_area = plot_w * plot_d
    required = sum(n.min_area for n in needs)
    if required * 1.05 > plot_area:
        raise DoesNotFitError(
            f"rooms need at least {required:.0f} m^2 but the plot is {plot_area:.0f} m^2 — increase plot size",
            required_area=required, plot_area=plot_area,
        )

    public = _order_group([n for n in needs if RoomType(n.type) in PUBLIC_ROOM_TYPES], _PUBLIC_ORDER, spec)
    private = _order_group([n for n in needs if RoomType(n.type) in PRIVATE_ROOM_TYPES], _PRIVATE_ORDER, spec)

    placed: list[tuple[RoomNeed, Rect]] = []
    try:
        for band_rect, group in _bands(plot_w, plot_d, facing, public, private):
            placed.extend(subdivide(group, band_rect, facing))
    except SubdivisionError as exc:
        raise DoesNotFitError(f"{exc} — increase plot size") from exc

    for need, rect in placed:  # leaf min-size gate (swap-tolerant)
        fits = (rect.w >= need.min_w - EPS and rect.d >= need.min_d - EPS) or (
            rect.w >= need.min_d - EPS and rect.d >= need.min_w - EPS
        )
        if not fits:
            raise DoesNotFitError(
                f"{need.label} would be {rect.w:.1f}x{rect.d:.1f} m, below its minimum "
                f"{need.min_w:.1f}x{need.min_d:.1f} m — increase plot size"
            )

    walls, wall_rooms = _build_walls(placed, plot_w, plot_d)
    doors = _place_doors(placed, walls, wall_rooms, spec, facing)

    # Round EDGES (not x/w independently) so adjacent rooms share the exact
    # same rounded coordinate — independent rounding lets edges drift apart by
    # >1 mm and register as phantom overlaps (caught by the property gate).
    rooms = [
        PlanRoom(
            id=need.key,
            type=RoomType(need.type),
            label=need.label,
            x=_round(rect.x), y=_round(rect.y),
            w=round(_round(rect.x2) - _round(rect.x), 3),
            h=round(_round(rect.y2) - _round(rect.y), 3),
            rotation=0,
        )
        for need, rect in placed
    ]
    return LayoutPlan(
        plot=PlanPlot(width_m=plot_w, depth_m=plot_d, facing=facing),
        rooms=rooms,
        walls=walls,
        doors=doors,
    )
