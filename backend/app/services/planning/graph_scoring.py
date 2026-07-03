"""Graph-satisfaction scoring (Sprint 18 Phase 4, first slice).

Measures how well a *generated layout* honours the adjacency relationships in
its ProgramGraph — the deterministic, explainable signal the roadmap leans on
instead of a learned solver. Given a graph (typically from
``from_parser_output``) and a generated layout dict, it checks, for each
MUST/SHOULD `adjacent` edge, whether the two rooms actually share a wall in the
layout, and returns a weighted satisfaction score plus the human-readable list
of unmet MUST adjacencies (for warnings).

Pure geometry + set logic, no ML. Additive: nothing here changes a generated
layout; it only inspects one.
"""
from dataclasses import dataclass, field

from app.services.planning.program_graph import ProgramGraph

# Two rooms count as adjacent if they share at least this much wall span on one
# axis and the perpendicular gap is within tolerance (absorbs partition-wall
# thickness / float drift at shared walls). A real corridor between them exceeds
# this, so corridor-connected rooms are correctly *not* counted as adjacent.
_MIN_SHARED_SPAN_M = 0.5
_GAP_TOLERANCE_M = 0.8

_SHOULD_WEIGHT = 0.4


# A room counts as reaching an exterior wall (daylight) if any of its footprint
# edges sits within this distance of the building boundary (absorbs boundary-wall
# thickness + float drift at shared walls).
_PERIMETER_TOLERANCE_M = 0.6


@dataclass
class GraphSatisfaction:
    must_total: int = 0
    must_satisfied: int = 0
    should_total: int = 0
    should_satisfied: int = 0
    score: float = 1.0  # weighted 0..1; 1.0 when there are no constraints
    unsatisfied_must: list[str] = field(default_factory=list)
    # Daylight / external-wall: spaces that need an exterior wall vs. how many
    # actually reach the building perimeter in the layout.
    daylight_total: int = 0
    daylight_satisfied: int = 0
    daylight_missing: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "mustTotal": self.must_total,
            "mustSatisfied": self.must_satisfied,
            "shouldTotal": self.should_total,
            "shouldSatisfied": self.should_satisfied,
            "score": round(self.score, 3),
            "unsatisfiedMust": list(self.unsatisfied_must),
            "daylightTotal": self.daylight_total,
            "daylightSatisfied": self.daylight_satisfied,
            "daylightMissing": list(self.daylight_missing),
        }


def _rooms_adjacent(a: dict, b: dict) -> bool:
    """True if two room dicts share a wall (AABB footprints, same floor)."""
    if a.get("floorLevel") != b.get("floorLevel"):
        return False
    try:
        ax, az = a["position"]["x"], a["position"]["z"]
        aw, ad = a["size"]["w"], a["size"]["d"]
        bx, bz = b["position"]["x"], b["position"]["z"]
        bw, bd = b["size"]["w"], b["size"]["d"]
    except (KeyError, TypeError):
        return False

    ax0, ax1 = ax - aw / 2, ax + aw / 2
    az0, az1 = az - ad / 2, az + ad / 2
    bx0, bx1 = bx - bw / 2, bx + bw / 2
    bz0, bz1 = bz - bd / 2, bz + bd / 2

    x_overlap = min(ax1, bx1) - max(ax0, bx0)
    z_overlap = min(az1, bz1) - max(az0, bz0)

    # Share a vertical wall (overlap on X, small gap on Z) or a horizontal wall.
    shares_x_wall = x_overlap >= _MIN_SHARED_SPAN_M and (-z_overlap) <= _GAP_TOLERANCE_M
    shares_z_wall = z_overlap >= _MIN_SHARED_SPAN_M and (-x_overlap) <= _GAP_TOLERANCE_M
    return shares_x_wall or shares_z_wall


def _floor_footprints(layout: dict) -> dict[int, dict]:
    """Map floor level -> footprint, falling back to the building footprint."""
    footprints: dict[int, dict] = {}
    for floor in layout.get("floors") or []:
        fp = floor.get("footprint")
        if fp:
            footprints[floor.get("level", 0)] = fp
    return footprints


def _room_on_perimeter(room: dict, footprint: dict) -> bool:
    """True if any edge of the room's footprint reaches the building boundary."""
    try:
        x, z = room["position"]["x"], room["position"]["z"]
        w, d = room["size"]["w"], room["size"]["d"]
    except (KeyError, TypeError):
        return False
    eps = _PERIMETER_TOLERANCE_M
    fx0, fx1 = footprint["x"], footprint["x"] + footprint["w"]
    fz0, fz1 = footprint["z"], footprint["z"] + footprint["d"]
    return (
        abs((x - w / 2) - fx0) <= eps
        or abs((x + w / 2) - fx1) <= eps
        or abs((z - d / 2) - fz0) <= eps
        or abs((z + d / 2) - fz1) <= eps
    )


def _layout_rooms_by_label(layout: dict) -> dict[str, dict]:
    """Map room label -> room dict from a layout (floors[].rooms preferred, with
    the flat top-level rooms as a fallback)."""
    rooms: dict[str, dict] = {}
    floors = layout.get("floors") or []
    if floors:
        for floor in floors:
            for room in floor.get("rooms") or []:
                label = room.get("label")
                if label:
                    rooms.setdefault(label, room)
    for room in layout.get("rooms") or []:
        label = room.get("label")
        if label:
            rooms.setdefault(label, room)
    return rooms


def score_graph_satisfaction(graph: ProgramGraph, layout: dict) -> GraphSatisfaction:
    result = GraphSatisfaction()
    rooms_by_label = _layout_rooms_by_label(layout)
    nodes_by_id = {n.id: n for n in graph.nodes}

    for edge in graph.edges:
        if edge.relation_type not in ("adjacent", "near"):
            continue
        node_a = nodes_by_id.get(edge.node_a)
        node_b = nodes_by_id.get(edge.node_b)
        if node_a is None or node_b is None:
            continue
        room_a = rooms_by_label.get(node_a.label)
        room_b = rooms_by_label.get(node_b.label)
        if room_a is None or room_b is None:
            # Can't evaluate a relationship whose rooms aren't in the layout.
            continue

        satisfied = _rooms_adjacent(room_a, room_b)
        if edge.strength == "MUST":
            result.must_total += 1
            if satisfied:
                result.must_satisfied += 1
            else:
                result.unsatisfied_must.append(
                    f"{node_a.label} ↔ {node_b.label}"
                )
        else:  # SHOULD (and any non-AVOID)
            result.should_total += 1
            if satisfied:
                result.should_satisfied += 1

    # Daylight / external-wall: every space that needs an exterior wall should
    # reach the building perimeter (else it's a windowless interior room).
    footprints = _floor_footprints(layout)
    if footprints:
        for node in graph.nodes:
            if not node.requires_external_wall:
                continue
            room = rooms_by_label.get(node.label)
            if room is None:
                continue
            footprint = footprints.get(room.get("floorLevel", 0))
            if footprint is None:
                continue
            result.daylight_total += 1
            if _room_on_perimeter(room, footprint):
                result.daylight_satisfied += 1
            else:
                result.daylight_missing.append(node.label)

    denom = result.must_total + _SHOULD_WEIGHT * result.should_total
    if denom > 0:
        numer = result.must_satisfied + _SHOULD_WEIGHT * result.should_satisfied
        result.score = numer / denom
    return result


def graph_satisfaction_dict(graph: ProgramGraph, layout: dict) -> dict:
    return score_graph_satisfaction(graph, layout).as_dict()
