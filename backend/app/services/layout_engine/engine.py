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
"""
import dataclasses

from app.config.mvp_defaults import (
    DEFAULT_FACING,
    DEFAULT_PLOT_DEPTH_M,
    DEFAULT_PLOT_WIDTH_M,
    DOOR_WIDTH_M,
    MAX_ROOMS_PER_LAYOUT,
    WALL_THICKNESS_M,
)
from app.schemas.layout_plan import Door, LayoutPlan, PlanPlot, PlanRoom, Wall
from app.schemas.requirements import Facing, RequirementsSpec, RoomType
from app.services import catalog
from app.services.layout_engine.archetypes import select_archetype, zoned_bands
from app.services.layout_engine.geometry import EPS, Rect, Segment
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError, subdivide
from app.services.planning import EngineProgram, from_requirements, to_engine_program
from app.services.planning.program_completion import ensure_corridor, ensure_entry

_MIN_DOOR_EDGE = DOOR_WIDTH_M + 0.1     # a door needs this much shared wall
_NARROW_DOOR_WIDTH = 0.7                # connectivity fallback on tight edges
_NARROW_DOOR_EDGE = _NARROW_DOOR_WIDTH + 0.1
_PRIVACY_THRESHOLD = 2  # matches quality.hard_constraints' own through_room_access threshold


class DoesNotFitError(ValueError):
    """Structured 'plot too small' error. Phase 4 maps this to a 422
    clarification ("increase plot size?")."""

    def __init__(self, message: str, *, required_area: float | None = None, plot_area: float | None = None):
        super().__init__(message)
        self.required_area = required_area
        self.plot_area = plot_area


# ── Expansion + zoning ────────────────────────────────────────────────────────


def _build_program(spec: RequirementsSpec, *, inject_corridor: bool = True) -> EngineProgram:
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
        if inject_corridor:
            graph = ensure_corridor(graph)
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
    return abs(w.x2 - w.x1) + abs(w.y2 - w.y1)


def _circulation_key(placed: list[tuple[RoomNeed, Rect]]) -> str:
    """The room the door graph roots at. Workflow Phase 4.4: a real
    corridor/hallway spine (`program_completion.ensure_corridor`) wins when
    one exists — routing "through the living room" was always a fiction for
    circulation, just a tolerable one while no program ever had a real
    corridor node. Falls back to the pre-4.4 behavior otherwise, so nothing
    changes for a program without one."""
    by_type = {n.type: n.key for n, _ in placed}
    for spine_type in ("corridor", "hallway"):
        if spine_type in by_type:
            return by_type[spine_type]
    if RoomType.living_room.value in by_type:
        return by_type[RoomType.living_room.value]
    if RoomType.entry.value in by_type:
        return by_type[RoomType.entry.value]
    return placed[0][0].key


def _pair_priority(pair: frozenset, zone_of: dict[str, str]) -> int:
    """Workflow Phase 4.4's connecting-wall preference order: circulation-to-
    room first, then public-to-public, everything else (routing through an
    arbitrary room) last. Used only to break ties in which pair the BFS
    spanning tree grows through next — connectivity itself is unaffected,
    only which walls end up hosting the doors that provide it."""
    zones = {zone_of.get(k, "semi_private") for k in pair}
    if "circulation" in zones:
        return 0
    if zones == {"public"}:
        return 1
    return 2


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
    # Workflow Phase 4.4: a `separated`/AVOID pair is vetoed from ever
    # getting a direct door, even when it would be the shortest way to
    # connect two otherwise-disconnected parts of the floor — connectivity
    # must route AROUND an explicit avoidance, not through it. Computed once,
    # used by both the spanning tree (step 2) and the "door every remaining
    # adjacent pair" pass (step 3, which already respected this).
    avoid_type_pairs = {frozenset((p.room_a.value, p.room_b.value)) for p in spec.avoid_adjacency}

    def is_avoided(pair: frozenset) -> bool:
        return frozenset(types_by_key[k] for k in pair) in avoid_type_pairs

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

    # 1.5. Guarantee any corridor/hallway spine has a door to a NON-PRIVATE
    #      neighbour, using its widest available shared wall even if narrow
    #      (below the usual narrow-door floor). Found live: the corridor's
    #      position is computed independently of the public band's own
    #      internal subdivision, so their shared edge can end up a genuine
    #      sliver by coincidence of proportions — without this, the BFS
    #      spanning tree (step 2 below) can end up bridging the corridor to
    #      the rest of the house ONLY through one of the private rooms it
    #      exists to serve, defeating the entire point of workflow 4.5's
    #      privacy-chain guarantee (every OTHER room the corridor serves
    #      becomes reachable only by passing through whichever private room
    #      happens to be that accidental bridge). A physically-real minimum
    #      still applies — this is a deliberately narrow service door, not
    #      an invented opening.
    _MIN_PHYSICAL_DOOR_EDGE = 0.4
    for corridor_key in (k for k, t in types_by_key.items() if t in ("corridor", "hallway")):
        candidates = [
            (pair, walls) for pair, walls in by_pair.items()
            if corridor_key in pair
            and catalog.privacy_level_for(types_by_key[next(iter(pair - {corridor_key}))]) < _PRIVACY_THRESHOLD
            and not is_avoided(pair)
        ]
        if not candidates:
            continue
        if any(w.id in doored_walls for _, walls in candidates for w in walls):
            continue  # already bridged to something non-private
        _, best_walls = max(candidates, key=lambda pw: max(_wall_length(w) for w in pw[1]))
        best = max(best_walls, key=_wall_length)
        if _wall_length(best) >= _MIN_DOOR_EDGE:
            add_door(best, DOOR_WIDTH_M)
        elif _wall_length(best) >= _NARROW_DOOR_EDGE:
            add_door(best, _NARROW_DOOR_WIDTH)
        elif _wall_length(best) >= _MIN_PHYSICAL_DOOR_EDGE:
            add_door(best, _wall_length(best))

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
        ranked_pairs = sorted(
            by_pair.items(),
            key=lambda kv: (_pair_priority(kv[0], zone_of), sorted(kv[0])),
        )
        for pair, pair_walls in ranked_pairs:
            a, b = sorted(pair)
            if (a in connected) == (b in connected):
                continue
            if is_avoided(pair):
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
    #    genuinely private (bedroom-bedroom, bedroom-pooja_room — privacy,
    #    not a defect) or the pair is explicitly avoided in the spec.
    #
    #    Uses catalog.privacy_level_for, NOT macro_zone — deliberately.
    #    macro_zone folds "service" into the same "private" bucket as
    #    genuinely private rooms (zoned_bands' banding wants that fold; see
    #    its own docstring), so a bedroom-bathroom pair used to get skipped
    #    here exactly like a bedroom-bedroom pair. That silently starved a
    #    private room of its only non-private neighbour whenever its sole
    #    other neighbour was a private-zoned room too — caught by workflow
    #    4.5's own privacy-chain check going red on a live Hypothesis
    #    counterexample (a pooja_room boxed in between a bedroom and a
    #    bathroom, both skipped here, forcing the spanning tree to route it
    #    through the bedroom). A bathroom at catalog privacy_level 1 is not
    #    "private" by the same definition the new check uses, so it must be
    #    allowed to bridge a private room to the rest of the house.
    for pair, pair_walls in by_pair.items():
        if is_avoided(pair):
            continue
        if all(catalog.privacy_level_for(types_by_key[k]) >= _PRIVACY_THRESHOLD for k in pair):
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


def generate_plan(spec: RequirementsSpec) -> LayoutPlan:
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

    def _place(prog: EngineProgram, archetype_fn) -> list[tuple[RoomNeed, Rect]]:
        result: list[tuple[RoomNeed, Rect]] = []
        for band_rect, group in archetype_fn(prog, plot_w, plot_d, facing).bands:
            result.extend(subdivide(group, band_rect, facing))
        return result

    archetype_key, archetype_fn, _ = select_archetype(program, spec.layout_style)
    active_program = program
    try:
        placed = _place(program, archetype_fn)
    except SubdivisionError as exc:
        if archetype_key == "zoned_bands":
            raise DoesNotFitError(f"{exc} — increase plot size") from exc
        # A more specific archetype (e.g. double_loaded_corridor's two
        # wings) can need more room along one axis than zoned_bands' single
        # progression does for the same program, purely from splitting into
        # more separate bands — found live on the clinic fixture, which
        # double_loaded_corridor's own selection criteria correctly match
        # but couldn't actually fit, while zoned_bands (the general-purpose
        # default every archetype falls back to) fit it fine. Try that
        # proven fallback once before giving up. Deliberately NOT a further
        # fallback to no-corridor placement: that would let generate_plan
        # return a plan with a real through_room_access violation on a
        # tight plot, silently breaking the exact guarantee workflow 4.5
        # exists for — an honest DoesNotFitError is the correct outcome
        # when even the general-purpose archetype can't fit the program
        # AND keep every private room genuinely reachable.
        try:
            placed = _place(program, zoned_bands)
        except SubdivisionError:
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
    doors = _place_doors(placed, walls, wall_rooms, spec, facing, active_program.zone_of)

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
