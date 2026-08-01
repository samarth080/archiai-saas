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
and which rooms go in each. Only ``zoned_bands`` exists so far;
``double_loaded_corridor``/``hub_and_spoke``/``open_core`` (workflow 3.1.b-d)
and graph-shape-based selection among several archetypes are deferred until
there is a second archetype to select between (YAGNI on the selector).
"""
from dataclasses import dataclass, field
from typing import Callable

from app.schemas.requirements import Facing
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


def zoned_bands(program: EngineProgram, plot_w: float, plot_d: float, facing: Facing) -> BandPlan:
    """Ordered zone progression, facing-anchored. Every band first gets its
    own minimum floor (see :func:`_band_floor`); whatever span is left over
    is then distributed across bands proportional to preferred-area share.
    This two-step "floor first, then slack by share" allocation — rather
    than peeling bands off one at a time and clamping each to its own floor
    as it goes — matters once there is more than one cut: a naive greedy
    peel can over-allocate an early band (rounding it up to its floor even
    though its true share is smaller) and starve a later one even when the
    *aggregate* of every band's floor comfortably fits the span. The
    two-band case reduces to materially the same split ``engine._bands``
    made. Raises ``SubdivisionError`` (same type ``subdivide`` raises, so
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
    if len(ordered_zones) == 1:
        return BandPlan(bands=[(Rect(0.0, 0.0, plot_w, plot_d), groups[ordered_zones[0]])])

    span, other = (plot_w, plot_d) if facing in (Facing.east, Facing.west) else (plot_d, plot_w)

    floors = {zone: _band_floor(rooms, other) for zone, rooms in groups.items()}
    total_floor = sum(floors.values())
    if total_floor > span + EPS:
        raise SubdivisionError(
            f"zones need at least {total_floor:.1f}m along the facing axis but the plot only has {span:.1f}m"
        )
    slack = span - total_floor
    areas = {zone: sum(n.preferred_area for n in rooms) for zone, rooms in groups.items()}
    total_area = sum(areas.values()) or 1.0
    lengths = {zone: floors[zone] + slack * areas[zone] / total_area for zone in ordered_zones}

    bands: list[tuple[Rect, list[RoomNeed]]] = []
    offset = 0.0
    for zone in ordered_zones:
        length = lengths[zone]
        bands.append((_zone_rect(plot_w, plot_d, facing, offset, length), groups[zone]))
        offset += length
    return BandPlan(bands=bands)


ArchetypeFn = Callable[[EngineProgram, float, float, Facing], BandPlan]
ARCHETYPES: dict[str, ArchetypeFn] = {"zoned_bands": zoned_bands}


def select_archetype(program: EngineProgram) -> tuple[str, ArchetypeFn, str]:
    """(archetype_key, fn, reason) — the doc's explainability rule (Phase
    3.2). ``zoned_bands`` is the only archetype implemented so far, so
    selection is trivial; graph-shape-based selection among several
    archetypes is deferred until a second one exists."""
    return "zoned_bands", zoned_bands, "only archetype implemented so far"
