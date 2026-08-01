"""ProgramGraph — a building-type-agnostic spatial program representation.

This is the spine the roadmap's later phases (graph-driven placement,
circulation, furniture) build on. It models a building as typed **spaces**
(and circulation / service / object / furniture / structural / opening nodes)
connected by **relationship edges** (adjacency, separation, circulation,
service dependency, …), independent of any residential vocabulary — an office,
clinic, or warehouse program is expressed exactly like a house.

Crucially it is *additive*: it sits alongside the existing
``parse_prompt -> RoomSpec -> generate_layout`` path via a lossless bridge
(:func:`from_parser_output` / :func:`to_room_specs`), so wiring it in does not
change any generated layout. See ``docs/NON_ML_GRAPH_LAYOUT_ENGINE.md``.

No ML anywhere — this is plain typed data + deterministic classification rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Iterable, Optional

from app.services import catalog
from app.services.layout_engine.subdivision import RoomNeed
from app.services.prompt_service import RoomSpec

if TYPE_CHECKING:  # avoid any import cost / cycles at runtime
    from app.services.building_template_service import BuildingTemplate
    from app.services.parser.constraint_extractor import AdjacencyConstraint
    from app.services.prompt_service import ParsedRequirements

# ── Vocabularies (building-type-agnostic classification) ─────────────────────

NodeType = str      # space | circulation | service | object | furniture | structural | opening
Zone = str          # public | private | semi_private | service | circulation | outdoor | technical

_CIRCULATION_TYPES = frozenset({
    "hallway", "corridor", "entry", "foyer", "lobby", "staircase", "stairs",
    "passage", "passageway", "landing", "atrium",
})
_SERVICE_TYPES = frozenset({
    "bathroom", "ensuite", "toilet", "washroom", "wc", "laundry", "storage",
    "utility", "garage", "mudroom", "pantry", "mechanical", "plant", "shaft",
    "store_room", "stock_room",
})
_WET_TYPES = frozenset({
    "bathroom", "ensuite", "toilet", "washroom", "wc", "kitchen", "kitchenette",
    "laundry", "utility", "pantry",
})
# Spaces that genuinely want an exterior wall / daylight.
_DAYLIGHT_TYPES = frozenset({
    "bedroom", "master_bedroom", "kids_room", "living_room", "open_plan_living",
    "office", "classroom", "consultation_room", "workspace", "dining_room",
    "study", "reception", "waiting_room", "meeting_room",
})
_OPEN_PLAN_TYPES = frozenset({
    "living_room", "open_plan_living", "kitchen", "dining_room", "dining_area",
    "workspace", "retail_display", "sales_floor",
})
_PUBLIC_TYPES = frozenset({
    "living_room", "open_plan_living", "kitchen", "dining_room", "dining_area",
    "foyer", "reception", "waiting_room", "retail_display", "checkout", "bar",
    "sales_floor", "classroom", "lobby",
})
_PRIVATE_TYPES = frozenset({
    "master_bedroom", "bedroom", "kids_room", "ensuite", "office",
    "consultation_room", "workspace", "meeting_room", "pooja_room",
    "meditation_room", "study",
})
_AVOID_TYPE_FAMILIES: dict[str, frozenset[str]] = {
    "bathroom": frozenset({"bathroom", "ensuite", "toilet", "washroom", "wc"}),
}


def _classify_node_type(space_type: str) -> NodeType:
    if space_type in _CIRCULATION_TYPES:
        return "circulation"
    if space_type in _SERVICE_TYPES:
        return "service"
    return "space"


def _classify_zone(space_type: str) -> Zone:
    if space_type in _CIRCULATION_TYPES:
        return "circulation"
    if space_type in _SERVICE_TYPES:
        return "service"
    if space_type in _PUBLIC_TYPES:
        return "public"
    if space_type in _PRIVATE_TYPES:
        return "private"
    return "semi_private"


# ── Node / Edge / Graph ──────────────────────────────────────────────────────


@dataclass
class Node:
    """A typed element of the building program. All fields default so partial
    construction (e.g. from an incomplete imported program) is always safe."""

    id: str = ""
    type: NodeType = "space"
    space_type: str = "generic"
    label: str = ""
    zone: Zone = "semi_private"
    target_area_sqm: Optional[float] = None
    min_area_sqm: Optional[float] = None
    max_area_sqm: Optional[float] = None
    size_hint: Optional[str] = None  # small | medium | large | xlarge — see to_engine_program
    width: Optional[float] = None
    depth: Optional[float] = None
    height: Optional[float] = None
    min_width_m: Optional[float] = None
    min_depth_m: Optional[float] = None
    preferred_aspect_ratio: Optional[float] = None
    floor_preference: str = "any"  # ground | upper | basement | any
    privacy_level: int = 0  # 0 public … 3 most private
    daylight_need: str = "none"  # none | low | medium | high
    acoustic_need: str = "none"
    wet_room: bool = False
    public_access: bool = True
    staff_only: bool = False
    requires_external_wall: bool = False
    can_be_open_plan: bool = False
    furniture_requirements: list[str] = field(default_factory=list)
    accessibility_requirements: list[str] = field(default_factory=list)
    source: str = "prompt"  # prompt | template | user_added | imported_program | inferred_rule


@dataclass
class Edge:
    node_a: str
    node_b: str
    relation_type: str = "adjacent"  # adjacent | near | separated | connected_by_door | ...
    strength: str = "SHOULD"  # MUST | SHOULD | AVOID
    preferred_relative_position: str = "any"
    min_shared_wall_m: float = 0.0
    door_required: bool = False
    access_required: bool = False
    visibility_required: bool = False
    reason: str = ""


@dataclass
class ProgramGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def add_node(self, node: Node) -> Node:
        if not node.id:
            node.id = f"node-{len(self.nodes)}"
        self.nodes.append(node)
        return node

    def add_edge(self, edge: Edge) -> Edge:
        self.edges.append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.id == node_id), None)

    def nodes_of_type(self, node_type: NodeType) -> list[Node]:
        return [n for n in self.nodes if n.type == node_type]

    def first_of_space_type(self, space_type: str) -> Optional[Node]:
        return next((n for n in self.nodes if n.space_type == space_type), None)

    def nodes_of_space_type(self, space_type: str) -> list[Node]:
        return [n for n in self.nodes if n.space_type == space_type]

    def buildable_nodes(self) -> list[Node]:
        """Nodes that occupy real floor area (everything except pure openings /
        structural markers) — the ones the bridge turns back into RoomSpecs."""
        return [n for n in self.nodes if n.type not in ("opening", "structural")]


def _apply_type_semantics(node: Node) -> Node:
    """Fill the derived boolean/daylight fields from the space_type."""
    st = node.space_type
    node.wet_room = st in _WET_TYPES
    node.can_be_open_plan = st in _OPEN_PLAN_TYPES
    if st in _DAYLIGHT_TYPES:
        node.requires_external_wall = True
        node.daylight_need = "high" if st in _PRIVATE_TYPES or st in _PUBLIC_TYPES else "medium"
    if node.zone == "private":
        node.privacy_level = 3
        node.public_access = False
    elif node.zone == "service":
        node.privacy_level = 2
    elif node.zone == "public":
        node.privacy_level = 0
    return node


def _constraint_nodes(
    graph: ProgramGraph,
    space_type: str,
    *,
    include_family: bool,
) -> list[Node]:
    types = (
        _AVOID_TYPE_FAMILIES.get(space_type, frozenset({space_type}))
        if include_family
        else frozenset({space_type})
    )
    return [node for node in graph.nodes if node.space_type in types]


# ── Adapters ─────────────────────────────────────────────────────────────────


def from_room_specs(room_specs: Iterable[RoomSpec], *, source: str = "prompt") -> ProgramGraph:
    """Build a graph whose buildable nodes are 1:1 with the given RoomSpecs, in
    order. This is the minimal, always-lossless construction."""
    graph = ProgramGraph()
    for spec in room_specs:
        node = Node(
            type=_classify_node_type(spec.room_type),
            space_type=spec.room_type,
            label=spec.label,
            zone=_classify_zone(spec.room_type),
            width=spec.w,
            depth=spec.d,
            height=spec.h,
            target_area_sqm=round(spec.w * spec.d, 2),
            source=source,
        )
        graph.add_node(_apply_type_semantics(node))
    return graph


def from_parser_output(parsed: "ParsedRequirements", room_specs: list[RoomSpec]) -> ProgramGraph:
    """Build a graph from the parser output.

    Buildable nodes are 1:1 with ``room_specs`` (preserving order/labels/dims),
    which is what makes :func:`to_room_specs` a lossless inverse. The parser's
    per-requirement zone/floor hints and adjacency constraints are attached as
    node attributes and edges — richer information that the bridge ignores but
    later graph-driven phases use.
    """
    graph = from_room_specs(room_specs, source="prompt")

    # Enrich nodes with the parser's per-room-type zone & floor preference.
    by_type: dict[str, object] = {}
    for req in getattr(parsed, "rooms", []) or []:
        by_type.setdefault(req.room_type, req)
    for node in graph.nodes:
        req = by_type.get(node.space_type)
        if req is not None:
            node.zone = getattr(req, "zone", node.zone) or node.zone
            node.floor_preference = getattr(req, "floor_preference", node.floor_preference)
            node.target_area_sqm = getattr(req, "area_m2", node.target_area_sqm)
            if node.target_area_sqm is not None:
                node.min_area_sqm = round(node.target_area_sqm * 0.6, 2)
                node.max_area_sqm = round(node.target_area_sqm * 1.5, 2)
            if node.width is not None:
                node.min_width_m = round(max(1.5, node.width * 0.6), 2)
            if node.depth is not None:
                node.min_depth_m = round(max(1.5, node.depth * 0.6), 2)
            if node.width and node.depth:
                node.preferred_aspect_ratio = round(
                    max(node.width, node.depth) / min(node.width, node.depth),
                    2,
                )
            _apply_type_semantics(node)

    explicit_daylight_types = set(getattr(parsed, "daylight_rooms", []) or [])
    for node in graph.nodes:
        if node.space_type in explicit_daylight_types:
            node.daylight_need = "high"
            node.requires_external_wall = True

    # Preserve every affected instance. The previous first-node-only bridge
    # silently ignored repeated bedrooms, classrooms, consultation rooms, and
    # other counted spaces during validation.
    for constraint in getattr(parsed, "adjacency_constraints", []) or []:
        include_family = constraint.strength == "AVOID"
        nodes_a = _constraint_nodes(
            graph,
            constraint.room_a,
            include_family=include_family,
        )
        nodes_b = _constraint_nodes(
            graph,
            constraint.room_b,
            include_family=include_family,
        )
        for a in nodes_a:
            for b in nodes_b:
                if a.id == b.id:
                    continue
                graph.add_edge(
                    Edge(
                        node_a=a.id,
                        node_b=b.id,
                        relation_type="adjacent",
                        strength=constraint.strength,
                        door_required=constraint.strength == "MUST",
                        reason=(
                            f"parser adjacency "
                            f"{constraint.room_a}~{constraint.room_b}"
                        ),
                    )
                )

    for room_a, room_b in getattr(parsed, "separation_constraints", []) or []:
        for a in graph.nodes_of_space_type(room_a):
            for b in graph.nodes_of_space_type(room_b):
                if a.id == b.id:
                    continue
                graph.add_edge(
                    Edge(
                        node_a=a.id,
                        node_b=b.id,
                        relation_type="separated",
                        strength="MUST",
                        reason=f"parser separation {room_a}~{room_b}",
                    )
                )
    return graph


def from_building_template(template: "BuildingTemplate") -> ProgramGraph:
    """Build a graph from a building template's default rooms + adjacency
    priorities. Useful as a starting program when the prompt is sparse."""
    graph = ProgramGraph()
    for room in template.default_rooms:
        for _ in range(max(1, room.minimum_count)):
            node = Node(
                type=_classify_node_type(room.room_type),
                space_type=room.room_type,
                label=room.label,
                zone=_classify_zone(room.room_type),
                width=room.w,
                depth=room.d,
                height=3.0,
                target_area_sqm=round(room.w * room.d, 2),
                source="template",
            )
            graph.add_node(_apply_type_semantics(node))
    for a_type, b_type in template.adjacency_priorities:
        a = graph.first_of_space_type(a_type)
        b = graph.first_of_space_type(b_type)
        if a is not None and b is not None and a.id != b.id:
            graph.add_edge(
                Edge(node_a=a.id, node_b=b.id, relation_type="adjacent", strength="SHOULD",
                     reason=f"template adjacency {a_type}~{b_type}")
            )
    return graph


def from_user_objects(canvas_objects: Iterable[dict]) -> ProgramGraph:
    """Build a graph from canvas objects (the editor's serialized rooms). Each
    object carries id/label/objectType/roomType/size."""
    graph = ProgramGraph()
    for obj in canvas_objects:
        size = obj.get("size") or {}
        space_type = obj.get("roomType") or obj.get("objectType") or "generic"
        node = Node(
            id=str(obj.get("id") or ""),
            type=_classify_node_type(space_type),
            space_type=space_type,
            label=obj.get("label") or space_type.replace("_", " ").title(),
            zone=_classify_zone(space_type),
            width=size.get("w"),
            depth=size.get("d"),
            height=size.get("h"),
            source="user_added",
        )
        if node.width and node.depth:
            node.target_area_sqm = round(node.width * node.depth, 2)
        graph.add_node(_apply_type_semantics(node))
    return graph


def merge(base: ProgramGraph, other: ProgramGraph) -> ProgramGraph:
    """Merge two graphs, de-duplicating nodes by id and re-basing colliding ids
    from ``other`` so no node is silently dropped."""
    merged = ProgramGraph(nodes=list(base.nodes), edges=list(base.edges))
    seen = {n.id for n in merged.nodes}
    remap: dict[str, str] = {}
    for node in other.nodes:
        new_id = node.id
        if not new_id or new_id in seen:
            new_id = f"node-{len(merged.nodes)}"
        if new_id != node.id:
            remap[node.id] = new_id
        node.id = new_id
        seen.add(new_id)
        merged.nodes.append(node)
    for edge in other.edges:
        merged.edges.append(
            Edge(
                node_a=remap.get(edge.node_a, edge.node_a),
                node_b=remap.get(edge.node_b, edge.node_b),
                relation_type=edge.relation_type,
                strength=edge.strength,
                preferred_relative_position=edge.preferred_relative_position,
                min_shared_wall_m=edge.min_shared_wall_m,
                door_required=edge.door_required,
                access_required=edge.access_required,
                visibility_required=edge.visibility_required,
                reason=edge.reason,
            )
        )
    return merged


# ── Bridge back to RoomSpec (lossless for the prompt path) ───────────────────


def to_room_specs(graph: ProgramGraph) -> list[RoomSpec]:
    """Convert a graph's buildable nodes back into RoomSpecs, preserving order.

    For a graph built via :func:`from_parser_output` / :func:`from_room_specs`
    this reproduces the original RoomSpec list exactly, so
    ``generate_layout(to_room_specs(from_parser_output(parsed, specs)))`` equals
    ``generate_layout(specs)``.
    """
    specs: list[RoomSpec] = []
    for node in graph.buildable_nodes():
        width = node.width
        depth = node.depth
        if width is None or depth is None:
            # Derive a square footprint from the target area when dims are absent.
            side = (node.target_area_sqm ** 0.5) if node.target_area_sqm else 3.0
            width = width if width is not None else round(side, 2)
            depth = depth if depth is not None else round(side, 2)
        specs.append(
            RoomSpec(
                label=node.label or node.space_type.replace("_", " ").title(),
                room_type=node.space_type,
                w=width,
                h=node.height if node.height is not None else 3.0,
                d=depth,
            )
        )
    return specs


# ── Bridge to EngineProgram (Phase 2.1 — additive; engine.py does not consume
# this yet, that is Phase 2.2) ────────────────────────────────────────────────

_SIZE_HINT_MULTIPLIERS = {"small": 0.7, "medium": 1.0, "large": 1.35, "xlarge": 1.75}
_ADJACENCY_RELATIONS = frozenset({"adjacent", "connected_by_door", "near"})
_ENTRY_TYPES = ("entry", "foyer", "lobby", "reception")
_FLOOR_BY_PREFERENCE = {"basement": -1, "ground": 0, "upper": 1, "any": 0}


@dataclass(frozen=True)
class EngineProgram:
    """Everything generation needs, derived from the graph. Pure data.

    This is what a future engine (Phase 2.2) consumes instead of a flat
    ``RequirementsSpec`` — building it here changes no generated layout.
    """

    needs: list[RoomNeed]
    zone_of: dict[str, str]
    must_adjacent: list[tuple[str, str]]
    should_adjacent: list[tuple[str, str]]
    avoid: list[tuple[str, str]]
    circulation_nodes: list[str]
    floor_of: dict[str, int]
    entry_node: Optional[str]


def _resolve_sizing(node: Node) -> tuple[float, float, float]:
    """(preferred_area, min_w, min_d) for one node.

    Precedence for the target/preferred area: explicit node area > size_hint
    x catalog multiplier > catalog default > derived from width/depth. Hard
    minima (min_w/min_d) never scale with size_hint — only explicit node
    minima override the catalog's.
    """
    try:
        space = catalog.get(node.space_type)
    except catalog.UnknownSpaceType:
        space = None

    if node.target_area_sqm is not None:
        area = node.target_area_sqm
    elif node.size_hint and space is not None:
        area = space.preferred_area_m2 * _SIZE_HINT_MULTIPLIERS[node.size_hint]
    elif space is not None:
        area = space.preferred_area_m2
    else:
        area = (node.width or 3.0) * (node.depth or 3.0)

    min_w = node.min_width_m if node.min_width_m is not None else (space.min_w if space else 1.2)
    min_d = node.min_depth_m if node.min_depth_m is not None else (space.min_d if space else 1.2)
    return round(area, 2), min_w, min_d


def _entry_node(nodes: list[Node]) -> Optional[str]:
    for candidate_type in _ENTRY_TYPES:
        for node in nodes:
            if node.space_type == candidate_type:
                return node.id
    return None


def _edge_buckets(
    edges: list[Edge],
) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    must: list[tuple[str, str]] = []
    should: list[tuple[str, str]] = []
    avoid: list[tuple[str, str]] = []
    for edge in edges:
        pair = (edge.node_a, edge.node_b)
        if edge.relation_type == "separated" or edge.strength == "AVOID":
            avoid.append(pair)
        elif edge.strength == "MUST" and edge.relation_type in _ADJACENCY_RELATIONS:
            must.append(pair)
        elif edge.strength == "SHOULD" and edge.relation_type in _ADJACENCY_RELATIONS:
            should.append(pair)
    return must, should, avoid


def to_engine_program(graph: ProgramGraph) -> EngineProgram:
    """Derive an :class:`EngineProgram` from a graph — id-level adjacency
    (not type-level), so e.g. two bedroom nodes each keep their own
    must/avoid pairs instead of collapsing onto "bedroom" as a type."""
    buildable = graph.buildable_nodes()
    needs: list[RoomNeed] = []
    zone_of: dict[str, str] = {}
    floor_of: dict[str, int] = {}
    for node in buildable:
        area, min_w, min_d = _resolve_sizing(node)
        needs.append(RoomNeed(
            key=node.id,
            type=node.space_type,
            label=node.label or node.space_type.replace("_", " ").title(),
            preferred_area=area,
            min_w=min_w,
            min_d=min_d,
        ))
        zone_of[node.id] = node.zone
        floor_of[node.id] = _FLOOR_BY_PREFERENCE.get(node.floor_preference, 0)

    must_adjacent, should_adjacent, avoid = _edge_buckets(graph.edges)
    circulation_nodes = [n.id for n in buildable if n.type == "circulation"]

    return EngineProgram(
        needs=needs,
        zone_of=zone_of,
        must_adjacent=must_adjacent,
        should_adjacent=should_adjacent,
        avoid=avoid,
        circulation_nodes=circulation_nodes,
        floor_of=floor_of,
        entry_node=_entry_node(buildable),
    )
