"""RequirementsSpec -> LayoutPlan orchestrator (workflow Step 1.2, banding
generalized in Phase 3.1a).

Pipeline: build the program graph (auto-entry, master rule is upstream in the
spec) -> archetypes.zoned_bands assigns rooms to an ordered N-zone band
progression (public/circulation/semi_private/service/private/..., driven by
the graph's own catalog-based zone_of, not a residential-only enum) -> split
the plot into those bands, facing-side first -> recursive subdivision per
band -> leaf min-size check (a room that would fall below its sizing-table
minimum raises DoesNotFitError — the structured "plot too small" the API
turns into a clarification) -> emit deduplicated walls (one wall per shared
edge) -> place doors (must-adjacency first, then a BFS spanning tree from the
circulation room so the access graph is connected by construction, plus the
front door on the entry's facing wall).

v0 limitations (documented, deliberate): single storey — `floors > 1` places
every room on one plot (the duplex case is an extraction/clarification concern,
not an engine one, until Section 17 work); rooms are emitted with rotation=0.

Polygon boundary path (workflow Phase 8): when `spec.plot.boundary` is set,
`generate_plan` dispatches to `_generate_plan_polygon` instead — a parallel
pipeline (own subdivider, own wall builder) that mirrors this one structurally
but operates on a general straight-edge polygon rather than plot_w x plot_d.
It is deliberately NOT unified with the rect path: GEOS/shapely floating-point
arithmetic is not guaranteed bit-identical to the exact `Rect` arithmetic this
file already leans on (see the "round EDGES, not x/w independently" comment
below — this file has been bitten by float-path drift before), so routing
every rectangular plot through shapely for a superficially cleaner abstraction
would mean re-proving float-for-float equivalence against the whole existing
test suite. Two smaller parallel functions is the safer, smaller diff.
`_place_doors` below is reused UNCHANGED by both paths — it only ever reads
`RoomNeed`/`Wall`/wall-length, never the shape type, confirmed genuinely
shape-agnostic.
"""
import dataclasses
import math

from app.config.mvp_defaults import (
    DEFAULT_FACING,
    DEFAULT_PLOT_DEPTH_M,
    DEFAULT_PLOT_WIDTH_M,
    DOOR_WIDTH_M,
    MAX_ROOMS_PER_LAYOUT,
    WALL_THICKNESS_M,
)
from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Vertex, Wall
from app.schemas.requirements import Facing, RequirementsSpec, RoomType
from app.services import catalog
from app.services.layout_engine import polygon
from app.services.layout_engine.archetypes import macro_zone, select_archetype
from app.services.layout_engine.geometry import EPS, Rect, Segment
from app.services.layout_engine.polygon_subdivision import subdivide_polygon
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError, subdivide
from app.services.planning import EngineProgram, from_requirements, to_engine_program
from app.services.planning.program_completion import ensure_entry

_MIN_DOOR_EDGE = DOOR_WIDTH_M + 0.1     # a door needs this much shared wall
_NARROW_DOOR_WIDTH = 0.7                # connectivity fallback on tight edges
_NARROW_DOOR_EDGE = _NARROW_DOOR_WIDTH + 0.1


class DoesNotFitError(ValueError):
    """Structured 'plot too small' error. Phase 4 maps this to a 422
    clarification ("increase plot size?")."""

    def __init__(self, message: str, *, required_area: float | None = None, plot_area: float | None = None):
        super().__init__(message)
        self.required_area = required_area
        self.plot_area = plot_area


# ── Expansion + zoning ────────────────────────────────────────────────────────


def _build_program(spec: RequirementsSpec) -> EngineProgram:
    """Program construction via the ProgramGraph bridge (workflow Phase 2.2b,
    extended in 3.1a): ``from_requirements`` builds the graph, ``ensure_entry``
    replaces the old inline auto-entry hack, ``to_engine_program`` derives the
    full :class:`EngineProgram` — the flat needs list subdivision consumes,
    plus ``zone_of``/``must_adjacent``/etc. that ``archetypes.zoned_bands`` now
    consumes for banding (Phase 2.2b only kept ``needs``, discarding the rest).
    Sizing/labels for a ``spec.rooms``-sourced program are byte-identical to
    the pre-graph version (see ``from_requirements``'s docstring for why it
    uses raw ``RoomType`` values and ``ROOM_SIZING``, not the catalog, for
    this path).

    Every node-id-keyed field is remapped from the graph's own node ids
    ("node-3") back to the legacy "r1".."rN" scheme, in the same list order
    the graph already produces (spec.rooms order, entry appended last if
    injected — matching the old dict-based ``_expand``'s insertion order
    exactly). This isn't cosmetic: ``_place_doors`` below tie-breaks its BFS
    spanning tree on the lexicographic sort of room keys, so a different key
    scheme can change *which* doors get placed, not just their id — confirmed
    by diffing against a pre-refactor golden snapshot of all 5 fixtures
    before this key remap was added.
    """
    try:
        graph = ensure_entry(from_requirements(spec))
    except catalog.UnknownSpaceType as exc:
        # `spec.spaces`'s free-string boundary (from_requirements validates
        # it eagerly) — translate into the existing clarification path
        # rather than a raw 500; `spec.rooms`'s closed RoomType enum can
        # never reach here (Pydantic already rejects an invalid value).
        raise DoesNotFitError(str(exc)) from exc
    program = to_engine_program(graph)
    remap = {need.key: f"r{i}" for i, need in enumerate(program.needs, start=1)}

    def _pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
        return [(remap[a], remap[b]) for a, b in pairs if a in remap and b in remap]

    return dataclasses.replace(
        program,
        needs=[dataclasses.replace(need, key=remap[need.key]) for need in program.needs],
        zone_of={remap[k]: v for k, v in program.zone_of.items() if k in remap},
        must_adjacent=_pairs(program.must_adjacent),
        should_adjacent=_pairs(program.should_adjacent),
        avoid=_pairs(program.avoid),
        circulation_nodes=[remap[k] for k in program.circulation_nodes if k in remap],
        floor_of={remap[k]: v for k, v in program.floor_of.items() if k in remap},
        entry_node=remap.get(program.entry_node),
    )


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
    # Euclidean, not Manhattan: a slanted polygon-boundary wall isn't
    # axis-aligned, and abs(dx)+abs(dy) understates/overstates its true
    # length, corrupting door-offset centering in _place_doors. A no-op for
    # every axis-aligned wall (Manhattan == Euclidean when one of dx/dy is
    # exactly zero) — verified byte-identical against all 5 fixtures.
    return math.hypot(w.x2 - w.x1, w.y2 - w.y1)


def _build_walls_polygon(placed: list[tuple[RoomNeed, "polygon.Polygon"]], plot_polygon: "polygon.Polygon"):
    """Polygon counterpart of `_build_walls` — same one-wall-per-shared-edge
    contract, computed via `polygon.shared_edges`/`polygon.is_on_boundary`
    instead of `Rect.shared_edge`/coordinate-vs-plot-span comparisons."""
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

    for i, (need_a, poly_a) in enumerate(placed):
        for need_b, poly_b in placed[i + 1:]:
            for seg in polygon.shared_edges(poly_a, poly_b):
                add(seg, need_a.key, need_b.key)

    for need, poly in placed:  # boundary portions belong to exactly one room
        coords = list(poly.exterior.coords)
        for (x1, y1), (x2, y2) in zip(coords, coords[1:]):
            mid = ((x1 + x2) / 2, (y1 + y2) / 2)
            if polygon.is_on_boundary(mid, plot_polygon):
                add(Segment(x1, y1, x2, y2), need.key, None)
    return walls, wall_rooms


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
    zone_of: dict[str, str],
    *,
    allow_disconnected: bool = False,
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
    if unreachable and not allow_disconnected:
        raise DoesNotFitError(
            f"no door-sized wall reaches: {', '.join(unreachable)} — increase plot size"
        )

    # 3. Direct doors between every remaining adjacent pair. Step 2 only adds
    #    the minimum doors needed for bare reachability (a spanning tree) —
    #    a room can be fully "reachable" while a wall it visibly shares with
    #    its next-door neighbour stays solid, which reads as broken
    #    connectivity even though nothing is technically unreachable (e.g. a
    #    dining room right next to the entry with no door between them,
    #    routed instead through the living room). Skip a pair only when
    #    there's a real reason not to connect them directly: both rooms are
    #    private/service-zoned (bedroom-bedroom, bedroom-bathroom — privacy,
    #    not a defect) or the pair is explicitly avoided in the spec.
    avoid_type_pairs = {frozenset((p.room_a.value, p.room_b.value)) for p in spec.avoid_adjacency}
    for pair, pair_walls in by_pair.items():
        pair_types = frozenset(types_by_key[k] for k in pair)
        if pair_types in avoid_type_pairs:
            continue
        if all(macro_zone(zone_of.get(k, "semi_private")) == "private" for k in pair):
            continue
        best = max(pair_walls, key=_wall_length)
        if _wall_length(best) >= _MIN_DOOR_EDGE:
            add_door(best, DOOR_WIDTH_M)
        elif _wall_length(best) >= _NARROW_DOOR_EDGE:
            add_door(best, _NARROW_DOOR_WIDTH)

    # 4. Front door on the entry's facing-side boundary wall (best effort).
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


def rebuild_derived_geometry(
    plan: LayoutPlan,
    spec: RequirementsSpec,
) -> LayoutPlan:
    """Recreate walls and doors from the plan's current room rectangles.

    Walls and doors are derived artifacts in the canonical ``LayoutPlan``
    contract. Editor geometry changes therefore invalidate any supplied copies.
    This helper deliberately permits disconnected edited states: it emits every
    valid hosted door it can, then lets the quality validator explain any rooms
    that remain unreachable. Initial generation remains strict.
    """

    if not plan.rooms:
        return plan.model_copy(update={"walls": [], "doors": []})

    placed: list[tuple[RoomNeed, Rect]] = []
    for room in plan.rooms:
        # Lenient lookup (never raises): an edited room's type could be any
        # catalog-known free string now, not just the 12 residential values
        # ROOM_SIZING covers — see `catalog.min_dimensions`'s own docstring
        # for why this stays permissive rather than rejecting the edit.
        min_w, min_d = catalog.min_dimensions(room.type)
        placed.append(
            (
                RoomNeed(
                    key=room.id,
                    type=room.type,
                    label=room.label,
                    preferred_area=room.w * room.h,
                    min_w=min_w,
                    min_d=min_d,
                ),
                Rect(room.x, room.y, room.w, room.h),
            )
        )

    walls, wall_rooms = _build_walls(
        placed,
        plan.plot.width_m,
        plan.plot.depth_m,
    )
    zone_of = {need.key: catalog.zone_for(need.type) for need, _ in placed}
    doors = _place_doors(
        placed,
        walls,
        wall_rooms,
        spec,
        plan.plot.facing,
        zone_of,
        allow_disconnected=True,
    )
    return plan.model_copy(update={"walls": walls, "doors": doors})


def _generate_plan_polygon(spec: RequirementsSpec) -> LayoutPlan:
    """Polygon counterpart of `generate_plan`'s tail — same validation order,
    same error types, no zone/archetype banding (Phase 8 scope: `zoned_bands`
    already collapses to one band for a single zone group, so subdividing the
    whole boundary as one band is the smallest thing that satisfies "rooms
    fill the boundary"; polygon-aware banding is deferred)."""
    facing = spec.facing or DEFAULT_FACING
    plot_polygon = polygon.polygon_from_vertices(spec.plot.boundary)
    if not plot_polygon.is_valid or not plot_polygon.is_simple or plot_polygon.area <= EPS:
        raise DoesNotFitError("plot boundary is not a valid simple polygon")

    program = _build_program(spec)
    needs = program.needs
    if not needs:
        raise DoesNotFitError("no rooms requested")
    if len(needs) > MAX_ROOMS_PER_LAYOUT:
        raise DoesNotFitError(f"more than {MAX_ROOMS_PER_LAYOUT} rooms requested")

    plot_area = plot_polygon.area
    required = sum(n.min_area for n in needs)
    if required * 1.05 > plot_area:
        raise DoesNotFitError(
            f"rooms need at least {required:.0f} m^2 but the plot is {plot_area:.0f} m^2 — increase plot size",
            required_area=required, plot_area=plot_area,
        )

    try:
        placed = subdivide_polygon(needs, plot_polygon, facing)
    except SubdivisionError as exc:
        raise DoesNotFitError(f"{exc} — increase plot size") from exc

    for need, poly in placed:  # leaf min-size gate (swap-tolerant), off the bbox
        minx, miny, maxx, maxy = poly.bounds
        w, d = maxx - minx, maxy - miny
        fits = (w >= need.min_w - EPS and d >= need.min_d - EPS) or (
            w >= need.min_d - EPS and d >= need.min_w - EPS
        )
        if not fits:
            raise DoesNotFitError(
                f"{need.label} would be {w:.1f}x{d:.1f} m, below its minimum "
                f"{need.min_w:.1f}x{need.min_d:.1f} m — increase plot size"
            )

    walls, wall_rooms = _build_walls_polygon(placed, plot_polygon)
    doors = _place_doors(placed, walls, wall_rooms, spec, facing, program.zone_of)

    rooms = []
    for need, poly in placed:
        minx, miny, maxx, maxy = poly.bounds
        x, y = _round(minx), _round(miny)
        w, h = round(_round(maxx) - x, 3), round(_round(maxy) - y, 3)
        vertices = None
        if not polygon.is_axis_aligned_rect(poly):
            ring = list(poly.exterior.coords)[:-1]  # drop the closing duplicate
            vertices = [Vertex(x=_round(px), y=_round(py)) for px, py in ring]
        rooms.append(PlanRoom(
            # `need.type` is already validated (see the rect path's own
            # comment above) — no RoomType(...) cast, same migration.
            id=need.key, type=need.type, label=need.label,
            x=x, y=y, w=w, h=h, rotation=0, vertices=vertices,
        ))

    plot_minx, plot_miny, plot_maxx, plot_maxy = plot_polygon.bounds
    boundary_ring = list(plot_polygon.exterior.coords)[:-1]
    return LayoutPlan(
        plot=PlanPlot(
            width_m=plot_maxx - plot_minx,
            depth_m=plot_maxy - plot_miny,
            facing=facing,
            boundary=[Vertex(x=_round(px), y=_round(py)) for px, py in boundary_ring],
        ),
        rooms=rooms,
        walls=walls,
        doors=doors,
    )


def generate_plan(spec: RequirementsSpec) -> LayoutPlan:
    if spec.plot.boundary is not None:
        return _generate_plan_polygon(spec)

    plot_w = spec.plot.width_m or DEFAULT_PLOT_WIDTH_M
    plot_d = spec.plot.depth_m or DEFAULT_PLOT_DEPTH_M
    facing = spec.facing or DEFAULT_FACING

    program = _build_program(spec)
    needs = program.needs
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

    placed: list[tuple[RoomNeed, Rect]] = []
    try:
        _, archetype_fn, _ = select_archetype(program, spec.layout_style)
        for band_rect, group in archetype_fn(program, plot_w, plot_d, facing).bands:
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
    doors = _place_doors(placed, walls, wall_rooms, spec, facing, program.zone_of)

    # Round EDGES (not x/w independently) so adjacent rooms share the exact
    # same rounded coordinate — independent rounding lets edges drift apart by
    # >1 mm and register as phantom overlaps (caught by the property gate).
    rooms = [
        PlanRoom(
            id=need.key,
            # `need.type` is already validated by this point — a raw RoomType
            # value from `spec.rooms` (Pydantic-enforced closed enum) or a
            # catalog-checked key from `spec.spaces` (`from_requirements`
            # calls `catalog.get()` eagerly) — no cast needed, and casting
            # via `RoomType(...)` would reject any non-residential type here.
            type=need.type,
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
