"""Pure, deterministic ProgramGraph-to-floor assignment."""

from dataclasses import dataclass

from app.services.planning.program_graph import Node, ProgramGraph

_MUST_ADJACENCY_RELATIONS = {"adjacent", "connected_by_door", "near"}
_GROUND_TYPES = {
    "entry",
    "foyer",
    "lobby",
    "reception",
    "living_room",
    "kitchen",
    "dining",
    "parking",
    "garage",
    "loading_dock",
    "waiting_room",
}
_UPPER_TYPES = {
    "bedroom",
    "master_bedroom",
    "private_office",
    "hotel_room",
    "guest_room",
}


@dataclass(frozen=True)
class FloorAssignmentReason:
    node_ids: tuple[str, ...]
    floor: int
    reason: str


@dataclass(frozen=True)
class FloorAssignment:
    floor_of: dict[str, int]
    reasons: tuple[FloorAssignmentReason, ...]


def _area(node: Node) -> float:
    return node.target_area_sqm or (node.width or 1.0) * (node.depth or 1.0)


def _must_components(graph: ProgramGraph) -> list[list[Node]]:
    nodes = graph.buildable_nodes()
    by_id = {node.id: node for node in nodes}
    parent = {node.id: node.id for node in nodes}

    def find(node_id: str) -> str:
        while parent[node_id] != node_id:
            parent[node_id] = parent[parent[node_id]]
            node_id = parent[node_id]
        return node_id

    def union(a: str, b: str) -> None:
        root_a, root_b = find(a), find(b)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)

    for edge in graph.edges:
        if (
            edge.strength == "MUST"
            and edge.relation_type in _MUST_ADJACENCY_RELATIONS
            and edge.node_a in parent
            and edge.node_b in parent
        ):
            union(edge.node_a, edge.node_b)

    grouped: dict[str, list[Node]] = {}
    for node_id, node in by_id.items():
        grouped.setdefault(find(node_id), []).append(node)
    return [
        sorted(group, key=lambda node: node.id)
        for _root, group in sorted(grouped.items())
    ]


def _floor_vote(node: Node) -> str | None:
    if node.floor_preference == "ground" or node.floor_preference == "basement":
        return "ground"
    if node.floor_preference == "upper":
        return "upper"
    if node.space_type in _GROUND_TYPES:
        return "ground"
    if node.space_type in _UPPER_TYPES:
        return "upper"
    return None


def _group_preference(group: list[Node], floors: int) -> tuple[str, str]:
    if floors == 1:
        return "ground", "single-floor program"

    ground_area = sum(_area(node) for node in group if _floor_vote(node) == "ground")
    upper_area = sum(_area(node) for node in group if _floor_vote(node) == "upper")
    if ground_area and upper_area:
        destination = "ground" if ground_area >= upper_area else "upper"
        return destination, (
            "MUST-linked floor preferences conflicted; kept the group together "
            f"on the {destination} side by moving the lighter side"
        )
    if ground_area:
        return "ground", "ground-floor preference"
    if upper_area:
        return "upper", "upper-floor preference"
    return "any", "balanced by target area"


def assign_floors(graph: ProgramGraph, floors: int) -> FloorAssignment:
    """Assign every buildable node to a zero-based floor.

    MUST adjacency components are indivisible. Explicit/type-derived day/night
    preferences are applied first; remaining components use largest-first
    load balancing. The input graph is never mutated.
    """
    if floors < 1:
        raise ValueError("floors must be at least 1")

    components = []
    for group in _must_components(graph):
        preference, reason = _group_preference(group, floors)
        components.append((group, preference, reason, sum(_area(node) for node in group)))
    components.sort(
        key=lambda item: (
            {"ground": 0, "upper": 1, "any": 2}[item[1]],
            -item[3],
            item[0][0].id,
        )
    )

    loads = [0.0] * floors
    floor_of: dict[str, int] = {}
    reasons: list[FloorAssignmentReason] = []
    for group, preference, reason, area in components:
        if preference == "ground":
            floor = 0
        elif preference == "upper":
            floor = min(range(1, floors), key=lambda index: (loads[index], index))
        else:
            floor = min(range(floors), key=lambda index: (loads[index], index))
        loads[floor] += area
        node_ids = tuple(node.id for node in group)
        floor_of.update({node_id: floor for node_id in node_ids})
        reasons.append(FloorAssignmentReason(node_ids=node_ids, floor=floor, reason=reason))

    return FloorAssignment(floor_of=floor_of, reasons=tuple(reasons))
