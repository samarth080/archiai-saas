"""Layout archetypes (workflow Phase 3.1a) — pure functions from an
``EngineProgram`` to a :class:`BandPlan` (which band holds which rooms).

``zoned_bands`` generalizes ``engine.py``'s old binary public/private split
(``_bands`` + ``_order_group`` + the residential-only ``PUBLIC_ROOM_TYPES``/
``PRIVATE_ROOM_TYPES`` frozensets) into the doc's "ordered zone progression
public -> semi_private -> private" — driven by the graph/catalog's own
``zone_of`` classification instead of the closed residential ``RoomType``
enum, so any building-type program the graph can represent bands correctly,
not just houses.

``zone_of`` itself is finer-grained than 3 tiers (``public|circulation|
semi_private|service|private|technical|outdoor``, see program_graph.py). An
earlier version of this module gave each of those its own top-level band —
tried against the real fixtures, it starved rooms on ordinary plot sizes: a
"public" band containing only kitchen+living (with entry/balcony/bathrooms
peeled into their own separate bands) came out narrower than kitchen's own
minimum width, even though the *aggregate* of every band's floor comfortably
fit the plot. Splitting a facing-side "circulation" band for something as
small as a foyer, or a same-size "service" band for two bathrooms, isn't how
real plans read anyway. So the 7-value ``zone_of`` is folded into the 3
*macro* bands the doc names (``_MACRO_ZONE``) before banding — circulation
joins public, service/technical/outdoor join private (unless a must-adjacency
redistribution moves a service node to its partner's band first).

Subdivision itself (``subdivision.subdivide``) is unchanged and shared by
every archetype; an archetype only decides band *structure* — the rectangles
and which rooms go in each.

``double_loaded_corridor``/``hub_and_spoke``/``open_core`` (workflow 3.1.b-d)
add three more band-structure functions plus the graph-shape selector
(3.2). None of them carve a literal circulation void: Phase 4 is what
actually injects a `corridor` program node and carves `corridor_rects` as
real rects (the field has existed on `BandPlan` since 3.1a and stays empty
here, same as before) — inventing an empty, room-less strip of floor area
before that exists would either leave a real gap in the tiled plot (breaking
the zero-gap guarantee every fixture/property test relies on) or require
fabricating a room nobody asked for. So here "corridor"/"hub"/"core" are
purely *band-grouping* ideas — which rooms cluster together and in what
shape — not carved voids; that's the honest, smaller thing that still makes
each archetype meaningfully different in code and in the resulting room
layout, without overclaiming Phase 4 geometry:

- ``double_loaded_corridor``: the public/circulation group anchors the
  facing edge (like ``zoned_bands``), but everything else is split into TWO
  parallel wings side by side (the perpendicular axis) instead of one deep
  band — alternating repeat units (bedrooms, classrooms, consultation
  rooms, ...) between them.
- ``hub_and_spoke``: the single highest-``circulation_weight`` public node
  becomes its own facing-anchored band (an "oversized center", sized the
  same floor-then-slack way every band is), must-adjacent spokes ordered
  first in the remaining band.
- ``open_core``: the single largest-area node (of any zone) anchors the
  facing edge; everyone else is one band behind it.

A literal ring/O-shaped hub-with-spokes-on-all-sides, or a true carved
corridor strip, both need real polygon/void support this engine's guillotine
subdivider does not have (and are exactly the kind of thing Phase 4's
`circulation.py` and Phase 10.2's polygon geometry exist for) — not
attempted here.
"""
from dataclasses import dataclass, field
from typing import Callable, Literal

from app.schemas.requirements import Facing
from app.services import catalog
from app.services.layout_engine.geometry import EPS, Rect
from app.services.layout_engine.subdivision import RoomNeed, SubdivisionError
from app.services.planning import EngineProgram

# zone_of value -> macro band, in facing-to-back order. Mirrors the old
# "entry leads the public band, service rooms sit with private" intent.
_MACRO_ZONE = {
    "circulation": "public",
    "public": "public",
    "semi_private": "semi_private",
    "service": "private",
    "private": "private",
    "technical": "private",
    "outdoor": "private",
}
_MACRO_ORDER = ("public", "semi_private", "private")
_MIN_BAND_SPAN = 1.5  # meters — same floor the old _bands() used


@dataclass(frozen=True)
class BandPlan:
    bands: list[tuple[Rect, list[RoomNeed]]]
    corridor_rects: list[tuple[str, Rect]] = field(default_factory=list)


def _macro_zone(zone: str) -> str:
    return _MACRO_ZONE.get(zone, "private")


def _redistribute_service(program: EngineProgram) -> dict[str, str]:
    """``zone_of``, with each service-zoned node reassigned to its
    must-adjacent partner's zone when one exists (an attached bathroom moves
    into its bedroom's band) — otherwise it keeps its own service zone and
    forms its own band with other unattached service rooms."""
    zone_of = dict(program.zone_of)
    reassign: dict[str, str] = {}
    for a, b in program.must_adjacent:
        za, zb = zone_of.get(a), zone_of.get(b)
        if za == "service" and zb and zb != "service":
            reassign[a] = zb
        if zb == "service" and za and za != "service":
            reassign[b] = za
    zone_of.update(reassign)
    return zone_of


def _pull_must_adjacent(rooms: list[RoomNeed], must_adjacent: list[tuple[str, str]]) -> list[RoomNeed]:
    """Reorder so each must-adjacent partner sits right after its anchor,
    within this one band's list — id-level (each room instance is handled on
    its own, not collapsed by type), the same soft-preference mechanism
    ``subdivision.subdivide`` already relies on list order for."""
    ordered = list(rooms)
    keys = {n.key for n in ordered}
    by_key = {n.key: n for n in ordered}
    for a, b in must_adjacent:
        if a not in keys or b not in keys:
            continue
        anchor, partner = by_key[a], by_key[b]
        if anchor is partner:
            continue
        ordered.remove(partner)
        ordered.insert(ordered.index(anchor) + 1, partner)
    return ordered


def _zone_rect(plot_w: float, plot_d: float, facing: Facing, offset: float, length: float) -> Rect:
    """The rect for a band starting ``offset`` meters from the facing edge
    and spanning ``length`` meters toward the back of the plot."""
    if facing == Facing.east:
        return Rect(plot_w - offset - length, 0.0, length, plot_d)
    if facing == Facing.west:
        return Rect(offset, 0.0, length, plot_d)
    if facing == Facing.south:
        return Rect(0.0, plot_d - offset - length, plot_w, length)
    return Rect(0.0, offset, plot_w, length)  # north


def _band_floor(rooms: list[RoomNeed], other: float) -> float:
    """Minimum band width along the facing (span) axis: the same
    area-derived floor ``engine._bands`` used, PLUS the shortest legal side
    of whichever room in this band needs the most room — without that second
    term a band can pass the aggregate-area check while still being too
    narrow for its single widest room (the same class of bug the Phase 4
    live-gate note above documents for cut clamping generally); mirrors
    ``subdivision._clamped_cut``'s own ``min_span_a``/``min_span_b`` guard."""
    if not rooms:
        return _MIN_BAND_SPAN
    min_span = max(min(n.min_w, n.min_d) for n in rooms)
    area_floor = sum(n.min_area for n in rooms) * 1.02 / other
    return max(_MIN_BAND_SPAN, min_span, area_floor)


def _facing_progression_bands(
    plot_w: float, plot_d: float, facing: Facing, ordered_groups: list[list[RoomNeed]],
) -> list[tuple[Rect, list[RoomNeed]]]:
    """Distribute ``ordered_groups`` (facing-edge group first) as consecutive
    bands along the facing progression axis. Every band first gets its own
    minimum floor (:func:`_band_floor`); whatever span is left over is then
    distributed across bands proportional to preferred-area share — see
    :func:`zoned_bands`'s original docstring for why "floor first, then
    slack by share" beats a naive greedy peel. Shared by every archetype
    that anchors an ordered group at the facing edge (``zoned_bands``'s zone
    progression, ``open_core``'s dominant/rest split, ``hub_and_spoke``'s
    hub/spokes split). Raises ``SubdivisionError`` when bands can't fit."""
    if len(ordered_groups) == 1:
        return [(Rect(0.0, 0.0, plot_w, plot_d), ordered_groups[0])]

    span, other = (plot_w, plot_d) if facing in (Facing.east, Facing.west) else (plot_d, plot_w)
    floors = [_band_floor(g, other) for g in ordered_groups]
    total_floor = sum(floors)
    if total_floor > span + EPS:
        raise SubdivisionError(
            f"zones need at least {total_floor:.1f}m along the facing axis but the plot only has {span:.1f}m"
        )
    slack = span - total_floor
    areas = [sum(n.preferred_area for n in g) for g in ordered_groups]
    total_area = sum(areas) or 1.0
    lengths = [f + slack * a / total_area for f, a in zip(floors, areas)]

    bands: list[tuple[Rect, list[RoomNeed]]] = []
    offset = 0.0
    for group, length in zip(ordered_groups, lengths):
        bands.append((_zone_rect(plot_w, plot_d, facing, offset, length), group))
        offset += length
    return bands


def _split_rect(rect: Rect, axis: str, groups: list[list[RoomNeed]]) -> list[Rect]:
    """Split ``rect`` into one sub-rect per group along ``axis`` ("w" or
    "d"), same floor-then-slack allocation as :func:`_facing_progression_bands`
    — used for the axis PERPENDICULAR to the facing progression
    (``double_loaded_corridor``'s two wings), where there is no facing-edge
    side to anchor against, just a left-to-right/top-to-bottom order."""
    span = rect.w if axis == "w" else rect.d
    other = rect.d if axis == "w" else rect.w
    floors = [_band_floor(g, other) for g in groups]
    total_floor = sum(floors)
    if total_floor > span + EPS:
        raise SubdivisionError(
            f"wings need at least {total_floor:.1f}m across but the available span is only {span:.1f}m"
        )
    slack = span - total_floor
    areas = [sum(n.preferred_area for n in g) for g in groups]
    total_area = sum(areas) or 1.0
    lengths = [f + slack * a / total_area for f, a in zip(floors, areas)]

    rects: list[Rect] = []
    offset = 0.0
    for length in lengths:
        if axis == "w":
            rects.append(Rect(rect.x + offset, rect.y, length, rect.d))
        else:
            rects.append(Rect(rect.x, rect.y + offset, rect.w, length))
        offset += length
    return rects


def _circulation_weight(space_type: str) -> float:
    try:
        return catalog.get(space_type).circulation_weight
    except catalog.UnknownSpaceType:
        return 1.0


def zoned_bands(program: EngineProgram, plot_w: float, plot_d: float, facing: Facing) -> BandPlan:
    """Ordered zone progression, facing-anchored — public/circulation
    leads, then semi_private, then private/service (see ``_MACRO_ZONE``).
    Raises ``SubdivisionError`` (same type ``subdivide`` raises, so
    ``engine.py``'s existing handler converts it) when bands can't fit."""
    if not program.needs:
        return BandPlan(bands=[])

    zone_of = _redistribute_service(program)
    groups: dict[str, list[RoomNeed]] = {}
    for need in program.needs:
        macro = _macro_zone(zone_of.get(need.key, "semi_private"))
        groups.setdefault(macro, []).append(need)
    for zone, rooms in groups.items():
        groups[zone] = _pull_must_adjacent(rooms, program.must_adjacent)

    ordered_zones = [z for z in _MACRO_ORDER if z in groups]
    ordered_groups = [groups[z] for z in ordered_zones]
    return BandPlan(bands=_facing_progression_bands(plot_w, plot_d, facing, ordered_groups))


def double_loaded_corridor(program: EngineProgram, plot_w: float, plot_d: float, facing: Facing) -> BandPlan:
    """Public/circulation group at the facing edge; everyone else split into
    two parallel wings (the perpendicular axis) instead of one deep private
    band — see the module docstring for why there is no literal carved
    corridor here yet. Degrades to a single facing-anchored band (same shape
    ``zoned_bands`` uses for one zone) when there's no public anchor or
    fewer than two rooms to split into wings."""
    if not program.needs:
        return BandPlan(bands=[])
    if len(program.needs) == 1:
        return BandPlan(bands=[(Rect(0.0, 0.0, plot_w, plot_d), list(program.needs))])

    zone_of = _redistribute_service(program)
    public = _pull_must_adjacent(
        [n for n in program.needs if _macro_zone(zone_of.get(n.key, "semi_private")) == "public"],
        program.must_adjacent,
    )
    public_keys = {n.key for n in public}
    repeat = _pull_must_adjacent(
        [n for n in program.needs if n.key not in public_keys],
        program.must_adjacent,
    )

    if not public or len(repeat) < 2:
        groups = [g for g in (public, repeat) if g]
        return BandPlan(bands=_facing_progression_bands(plot_w, plot_d, facing, groups))

    public_band, (wings_rect, _) = _facing_progression_bands(plot_w, plot_d, facing, [public, repeat])

    wing_a, wing_b = repeat[0::2], repeat[1::2]
    wing_groups = [g for g in (wing_a, wing_b) if g]
    if len(wing_groups) < 2:
        return BandPlan(bands=[public_band, (wings_rect, repeat)])

    perp_axis = "d" if facing in (Facing.east, Facing.west) else "w"
    wing_rects = _split_rect(wings_rect, perp_axis, wing_groups)
    return BandPlan(bands=[public_band] + list(zip(wing_rects, wing_groups)))


def hub_and_spoke(program: EngineProgram, plot_w: float, plot_d: float, facing: Facing) -> BandPlan:
    """The highest-``circulation_weight`` public node (waiting room,
    reception, lobby — falls back to any node if there's no public one)
    becomes its own facing-anchored band; must-adjacent spokes are ordered
    first in the remaining band."""
    if not program.needs:
        return BandPlan(bands=[])
    if len(program.needs) == 1:
        return BandPlan(bands=[(Rect(0.0, 0.0, plot_w, plot_d), list(program.needs))])

    candidates = [
        n for n in program.needs if _macro_zone(program.zone_of.get(n.key, "semi_private")) == "public"
    ] or list(program.needs)
    hub = max(candidates, key=lambda n: (_circulation_weight(n.type), n.preferred_area))

    # `_pull_must_adjacent` reorders relative to an anchor INSIDE the same
    # list — the hub isn't part of `others`, so a plain call can't move a
    # hub-spoke pair. Sort hub-must-partners first instead (stable sort
    # keeps everything else in its original order), then still run
    # `_pull_must_adjacent` so must-adjacency BETWEEN spokes is honoured too.
    others = [n for n in program.needs if n.key != hub.key]
    hub_partners = {b if a == hub.key else a for a, b in program.must_adjacent if hub.key in (a, b)}
    others.sort(key=lambda n: n.key not in hub_partners)
    spokes = _pull_must_adjacent(others, program.must_adjacent)
    return BandPlan(bands=_facing_progression_bands(plot_w, plot_d, facing, [[hub], spokes]))


def open_core(program: EngineProgram, plot_w: float, plot_d: float, facing: Facing) -> BandPlan:
    """The single largest-area node (any zone — an open workspace, retail
    floor, warehouse volume) anchors the facing edge; everyone else forms
    one service-cluster band behind it."""
    if not program.needs:
        return BandPlan(bands=[])
    if len(program.needs) == 1:
        return BandPlan(bands=[(Rect(0.0, 0.0, plot_w, plot_d), list(program.needs))])

    dominant = max(program.needs, key=lambda n: n.preferred_area)
    rest = _pull_must_adjacent(
        [n for n in program.needs if n.key != dominant.key],
        program.must_adjacent,
    )
    return BandPlan(bands=_facing_progression_bands(plot_w, plot_d, facing, [[dominant], rest]))


ArchetypeFn = Callable[[EngineProgram, float, float, Facing], BandPlan]
ARCHETYPES: dict[str, ArchetypeFn] = {
    "zoned_bands": zoned_bands,
    "double_loaded_corridor": double_loaded_corridor,
    "hub_and_spoke": hub_and_spoke,
    "open_core": open_core,
}
LayoutStyle = Literal["zoned_bands", "double_loaded_corridor", "hub_and_spoke", "open_core"]

_MIN_REPEAT_UNITS = 3  # "≥3 same-type private/semi nodes" (workflow 3.1.b)
_MIN_HUB_SPOKES = 3    # "a single dominant public node with ≥3 MUST spokes" (3.1.c)
_MIN_DOMINANT_SHARE = 0.5  # "one node ≥50% of area" (3.1.d)

# A spine-shaped circulation node — NOT the full program_graph.py
# `_CIRCULATION_TYPES` set. That set also includes "entry"/"foyer"/"lobby"/
# "staircase", which `program_completion.ensure_entry` injects into
# virtually every program, residential ones included; gating on "any
# circulation node" made every 3+-bedroom house silently select
# double_loaded_corridor the moment this file was written (caught by
# actually running the 5 requirement fixtures through this selector before
# committing, not assumed safe — 4bhk has 3 bedrooms + an auto-injected
# entry, and would otherwise have flipped). A double-loaded corridor is
# specifically a hallway/corridor SPINE with rooms on both sides, so it
# should require one of those, not just "the program has an entry."
_CORRIDOR_SPINE_TYPES = frozenset({"hallway", "corridor", "passage", "passageway"})


def select_archetype(
    program: EngineProgram, layout_style: LayoutStyle | None = None,
) -> tuple[str, ArchetypeFn, str]:
    """(archetype_key, fn, reason) — the doc's explainability rule (Phase
    3.2). An explicit ``layout_style`` always wins; otherwise selection reads
    graph SHAPE, not ``building_type`` vocabulary, so an untemplated program
    still lands on a sane archetype. Rules, in order (first match wins):

    1. ≥3 same-type repeat units in the semi_private/private zones, plus a
       hallway/corridor spine node in the program → ``double_loaded_corridor``.
    2. A public node with ≥3 MUST-adjacent spokes → ``hub_and_spoke``.
    3. A single node holding ≥50% of the program's total area → ``open_core``.
    4. Otherwise → ``zoned_bands`` (the general-purpose default).
    """
    if layout_style is not None:
        return layout_style, ARCHETYPES[layout_style], f"explicit layout_style={layout_style!r}"

    if not program.needs:
        return "zoned_bands", zoned_bands, "empty program — default archetype"

    repeat_counts: dict[str, int] = {}
    for need in program.needs:
        if _macro_zone(program.zone_of.get(need.key, "semi_private")) in ("semi_private", "private"):
            repeat_counts[need.type] = repeat_counts.get(need.type, 0) + 1
    repeated_type = next((t for t, count in repeat_counts.items() if count >= _MIN_REPEAT_UNITS), None)
    has_corridor_spine = any(n.type in _CORRIDOR_SPINE_TYPES for n in program.needs)
    if repeated_type is not None and has_corridor_spine:
        return (
            "double_loaded_corridor", double_loaded_corridor,
            f"{repeat_counts[repeated_type]} {repeated_type!r} units plus a hallway/corridor spine in the program",
        )

    public_needs = [
        n for n in program.needs if _macro_zone(program.zone_of.get(n.key, "semi_private")) == "public"
    ]
    if public_needs:
        hub = max(public_needs, key=lambda n: (_circulation_weight(n.type), n.preferred_area))
        spoke_count = sum(1 for a, b in program.must_adjacent if hub.key in (a, b))
        if spoke_count >= _MIN_HUB_SPOKES:
            return (
                "hub_and_spoke", hub_and_spoke,
                f"{hub.label!r} is a public hub with {spoke_count} MUST-adjacent spokes",
            )

    total_area = sum(n.preferred_area for n in program.needs) or 1.0
    dominant = max(program.needs, key=lambda n: n.preferred_area)
    dominant_share = dominant.preferred_area / total_area
    if dominant_share >= _MIN_DOMINANT_SHARE:
        return (
            "open_core", open_core,
            f"{dominant.label!r} is {dominant_share:.0%} of the program's total area",
        )

    return "zoned_bands", zoned_bands, "no archetype-specific graph shape matched"
