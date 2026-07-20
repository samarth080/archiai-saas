"""Deterministic, explainable ProgramGraph constraint evaluation.

The scorer evaluates the final layout geometry for every supported graph edge.
It keeps the original aggregate adjacency ratios for compatibility and adds
typed per-constraint results that Program Check and later editor validation can
reuse. No placement or rendering decisions happen here.
"""
from dataclasses import dataclass, field
from typing import Literal

from app.services.planning.program_graph import ProgramGraph

_MIN_SHARED_SPAN_M = 0.5
_GAP_TOLERANCE_M = 0.8
_SHOULD_WEIGHT = 0.4

ConstraintStatus = Literal[
    "satisfied",
    "warning",
    "failed",
    "not_evaluated",
    "missing_dependency",
]


@dataclass(frozen=True)
class ConstraintCheck:
    id: str
    relation_type: str
    strength: str
    node_a: str
    node_b: str
    label: str
    status: ConstraintStatus
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "relationType": self.relation_type,
            "strength": self.strength,
            "nodeA": self.node_a,
            "nodeB": self.node_b,
            "label": self.label,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class GraphSatisfaction:
    must_total: int = 0
    must_satisfied: int = 0
    should_total: int = 0
    should_satisfied: int = 0
    avoid_total: int = 0
    avoid_satisfied: int = 0
    score: float = 1.0
    unsatisfied_must: list[str] = field(default_factory=list)
    checks: list[ConstraintCheck] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "mustTotal": self.must_total,
            "mustSatisfied": self.must_satisfied,
            "shouldTotal": self.should_total,
            "shouldSatisfied": self.should_satisfied,
            "avoidTotal": self.avoid_total,
            "avoidSatisfied": self.avoid_satisfied,
            "score": round(self.score, 3),
            "unsatisfiedMust": list(self.unsatisfied_must),
            "checks": [check.as_dict() for check in self.checks],
        }


def _rooms_adjacent(a: dict, b: dict) -> bool:
    """Return true only when two same-floor AABBs share a usable wall span."""
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
    z_edge_gap = min(abs(az1 - bz0), abs(bz1 - az0))
    x_edge_gap = min(abs(ax1 - bx0), abs(bx1 - ax0))

    return (
        x_overlap >= _MIN_SHARED_SPAN_M and z_edge_gap <= _GAP_TOLERANCE_M
    ) or (
        z_overlap >= _MIN_SHARED_SPAN_M and x_edge_gap <= _GAP_TOLERANCE_M
    )


def _layout_rooms_by_label(layout: dict) -> dict[str, dict]:
    """Map unique generated room labels to their final geometry."""
    rooms: dict[str, dict] = {}

    def add_room(room: dict) -> None:
        if room.get("objectType") not in (None, "room"):
            return
        label = room.get("label")
        if label:
            rooms.setdefault(label, room)

    for floor in layout.get("floors") or []:
        for room in floor.get("rooms") or []:
            add_room(room)
    for room in layout.get("rooms") or []:
        add_room(room)
    return rooms


def _missing_check(
    index: int,
    relation_type: str,
    strength: str,
    label_a: str,
    label_b: str,
    reason: str,
) -> ConstraintCheck:
    return ConstraintCheck(
        id=f"constraint-{index + 1}",
        relation_type=relation_type,
        strength=strength,
        node_a=label_a,
        node_b=label_b,
        label=f"{label_a} / {label_b}",
        status="missing_dependency",
        reason=reason or "One or both requested spaces are missing from the layout.",
    )


def score_graph_satisfaction(graph: ProgramGraph, layout: dict) -> GraphSatisfaction:
    result = GraphSatisfaction()
    rooms_by_label = _layout_rooms_by_label(layout)
    nodes_by_id = {node.id: node for node in graph.nodes}

    weighted_total = 0.0
    weighted_satisfied = 0.0

    for index, edge in enumerate(graph.edges):
        node_a = nodes_by_id.get(edge.node_a)
        node_b = nodes_by_id.get(edge.node_b)
        if node_a is None or node_b is None:
            result.checks.append(
                _missing_check(
                    index,
                    edge.relation_type,
                    edge.strength,
                    edge.node_a,
                    edge.node_b,
                    edge.reason,
                )
            )
            continue

        room_a = rooms_by_label.get(node_a.label)
        room_b = rooms_by_label.get(node_b.label)
        labels = f"{node_a.label} \u2194 {node_b.label}"
        is_apart_rule = edge.strength == "AVOID" or edge.relation_type == "separated"
        is_supported = edge.relation_type in ("adjacent", "near", "separated")

        if is_supported is False:
            result.checks.append(
                ConstraintCheck(
                    id=f"constraint-{index + 1}",
                    relation_type=edge.relation_type,
                    strength=edge.strength,
                    node_a=node_a.label,
                    node_b=node_b.label,
                    label=labels,
                    status="not_evaluated",
                    reason=edge.reason or "This relationship is not geometrically evaluated yet.",
                )
            )
            continue

        if is_apart_rule:
            result.avoid_total += 1
            weighted_total += 1.0
        elif edge.strength == "MUST" and is_supported:
            result.must_total += 1
            weighted_total += 1.0
        elif edge.strength == "SHOULD" and is_supported:
            result.should_total += 1
            weighted_total += _SHOULD_WEIGHT

        if room_a is None or room_b is None:
            result.checks.append(
                _missing_check(
                    index,
                    edge.relation_type,
                    edge.strength,
                    node_a.label,
                    node_b.label,
                    edge.reason,
                )
            )
            if edge.strength == "MUST" and not is_apart_rule:
                result.unsatisfied_must.append(labels)
            continue

        adjacent = _rooms_adjacent(room_a, room_b)
        satisfied = not adjacent if is_apart_rule else adjacent
        if satisfied:
            weighted_satisfied += 1.0 if is_apart_rule or edge.strength == "MUST" else _SHOULD_WEIGHT
            if is_apart_rule:
                result.avoid_satisfied += 1
            elif edge.strength == "MUST":
                result.must_satisfied += 1
            else:
                result.should_satisfied += 1
            status: ConstraintStatus = "satisfied"
        elif edge.strength == "SHOULD" and not is_apart_rule:
            status = "warning"
        else:
            status = "failed"
            if edge.strength == "MUST" and not is_apart_rule:
                result.unsatisfied_must.append(labels)

        if is_apart_rule:
            action = "Keep apart"
        elif edge.strength == "MUST":
            action = "Must be adjacent"
        else:
            action = "Should be adjacent"
        result.checks.append(
            ConstraintCheck(
                id=f"constraint-{index + 1}",
                relation_type=edge.relation_type,
                strength=edge.strength,
                node_a=node_a.label,
                node_b=node_b.label,
                label=f"{action}: {node_a.label} / {node_b.label}",
                status=status,
                reason=edge.reason,
            )
        )

    if weighted_total > 0:
        result.score = weighted_satisfied / weighted_total
    return result


def graph_satisfaction_dict(graph: ProgramGraph, layout: dict) -> dict:
    return score_graph_satisfaction(graph, layout).as_dict()
