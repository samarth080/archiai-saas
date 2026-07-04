"""Graph layout orchestration (Phase 4 Stages 1, 4-8).

`prepare` (Stage 1) turns a ProgramGraph + pattern rules into a `PreparedGraph`:
buildable nodes with complete numeric fields and a single unified, de-duplicated
edge list (graph edges + pattern-rule adjacencies, with the MUST-over-AVOID
conflict rule). Deterministic throughout — everything iterates sorted keys.

Must not import layout_service (kept acyclic); footprint constants live in
boundary.py. The per-floor placement (`place_floor`, Stages 4-8) is added next.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from app.services.layout_pattern_service import LayoutPatternRules
from app.services.planning.program_graph import ProgramGraph
from app.services.planning.slicing_tree import Item, SliceEdge
from app.services.planning.validation import validate

_MIN_DIM = 1.5

# ProgramGraph relation → SliceEdge relation. Rank orders conflict resolution
# (higher wins); AVOID is the odd one out (opposite intent) and ranks lowest so
# an explicit adjacency overrides a pattern-implied separation.
_RELATION_RANK = {"must": 4, "should": 3, "near": 2, "visual": 1, "avoid": 0}


@dataclass(frozen=True)
class PreparedNode:
    id: str
    space_type: str
    label: str
    zone: str
    area: float
    width: float
    depth: float
    height: float
    min_w: float
    min_d: float
    needs_external: bool
    wet_room: bool
    floor_preference: str

    def to_item(self) -> Item:
        return Item(
            id=self.id,
            area=self.area,
            min_w=self.min_w,
            min_d=self.min_d,
            needs_external=self.needs_external,
        )


@dataclass(frozen=True)
class PreparedGraph:
    nodes: tuple[PreparedNode, ...]
    edges: tuple[SliceEdge, ...]
    warnings: tuple[str, ...]

    def node(self, node_id: str) -> PreparedNode | None:
        return next((n for n in self.nodes if n.id == node_id), None)


def _prepare_node(node) -> PreparedNode:
    width = node.width if node.width else None
    depth = node.depth if node.depth else None
    if width is None or depth is None:
        side = sqrt(node.target_area_sqm) if node.target_area_sqm else 3.0
        width = width or round(side, 2)
        depth = depth or round(side, 2)
    area = node.target_area_sqm or round(width * depth, 2)
    return PreparedNode(
        id=node.id,
        space_type=node.space_type,
        label=node.label or node.space_type.replace("_", " ").title(),
        zone=node.zone or "other",
        area=area,
        width=width,
        depth=depth,
        height=node.height or 3.0,
        min_w=max(_MIN_DIM, node.min_width_m or 0.0),
        min_d=max(_MIN_DIM, node.min_depth_m or 0.0),
        needs_external=bool(node.requires_external_wall),
        wet_room=bool(node.wet_room),
        floor_preference=node.floor_preference or "any",
    )


def _map_relation(strength: str, relation_type: str) -> str:
    if strength == "AVOID" or relation_type == "separated":
        return "avoid"
    if relation_type == "near":
        return "near"
    if relation_type == "visual_connection":
        return "visual"
    if strength == "MUST":
        return "must"
    return "should"


def _unify_edges(
    graph: ProgramGraph,
    nodes: list[PreparedNode],
    pattern_rules: LayoutPatternRules | None,
    warnings: list[str],
) -> list[SliceEdge]:
    node_ids = {n.id for n in nodes}
    by_type: dict[str, list[PreparedNode]] = {}
    for n in nodes:
        by_type.setdefault(n.space_type, []).append(n)

    # pair -> {relation: rel_pos} candidates
    candidates: dict[tuple[str, str], dict[str, str]] = {}

    def add(a: str, b: str, relation: str, rel_pos: str = "any"):
        if a == b or a not in node_ids or b not in node_ids:
            return
        key = (a, b) if a < b else (b, a)
        candidates.setdefault(key, {}).setdefault(relation, rel_pos)

    # 1. Explicit ProgramGraph edges.
    for edge in graph.edges:
        add(
            edge.node_a,
            edge.node_b,
            _map_relation(edge.strength, edge.relation_type),
            edge.preferred_relative_position or "any",
        )

    # 2. Pattern-rule adjacencies/avoidances → node-level SHOULD / AVOID edges
    #    (first node of each matching type, deterministically).
    if pattern_rules is not None:
        for a in sorted(nodes, key=lambda n: n.id):
            rule = pattern_rules.rule_for(a.space_type)
            for target in rule.adjacent_to:
                for b in by_type.get(target, []):
                    add(a.id, b.id, "should")
            for target in rule.avoid_adjacent_to:
                for b in by_type.get(target, []):
                    add(a.id, b.id, "avoid")

    # 3. Resolve each pair to a single edge (highest rank wins; MUST over AVOID
    #    warns), processed in sorted order for determinism.
    edges: list[SliceEdge] = []
    for key in sorted(candidates):
        relations = candidates[key]
        best = max(relations, key=lambda r: _RELATION_RANK.get(r, 0))
        if best == "must" and "avoid" in relations:
            warnings.append(
                f"Conflicting rules for {key[0]}-{key[1]}: adjacency required, separation dropped"
            )
        edges.append(SliceEdge(a=key[0], b=key[1], relation=best, rel_pos=relations[best]))
    return edges


def prepare(
    graph: ProgramGraph,
    pattern_rules: LayoutPatternRules | None = None,
) -> PreparedGraph:
    warnings = [w.message for w in validate(graph)]
    nodes = [_prepare_node(node) for node in graph.buildable_nodes()]
    edges = _unify_edges(graph, nodes, pattern_rules, warnings)
    return PreparedGraph(tuple(nodes), tuple(edges), tuple(warnings))
