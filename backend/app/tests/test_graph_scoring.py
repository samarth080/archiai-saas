"""Graph-satisfaction scoring (Sprint 18 Phase 4)."""
import pytest

from app.services.layout_service import generate_layout
from app.services.planning import (
    Edge,
    Node,
    ProgramGraph,
    from_parser_output,
    score_graph_satisfaction,
)
from app.services.planning.graph_scoring import _rooms_adjacent
from app.services.prompt_service import parse_prompt, parsed_to_room_specs


def _room(label, x, z, w=4.0, d=4.0, floor=0):
    return {
        "label": label,
        "floorLevel": floor,
        "position": {"x": x, "y": 1.5, "z": z},
        "size": {"w": w, "h": 3.0, "d": d},
    }


# ── Adjacency geometry ────────────────────────────────────────────────────────


def test_rooms_sharing_a_wall_are_adjacent():
    a = _room("A", 0, 0)   # x in [-2, 2]
    b = _room("B", 4, 0)   # x in [2, 6] — shares the wall at x=2
    assert _rooms_adjacent(a, b) is True


def test_far_apart_rooms_are_not_adjacent():
    a = _room("A", 0, 0)
    far = _room("C", 20, 0)
    assert _rooms_adjacent(a, far) is False


def test_corridor_gap_breaks_adjacency():
    a = _room("A", 0, 0)      # x in [-2, 2]
    across = _room("E", 7, 0)  # x in [5, 9] — a 3 m gap, wider than tolerance
    assert _rooms_adjacent(a, across) is False


def test_rooms_on_different_floors_are_not_adjacent():
    a = _room("A", 0, 0, floor=0)
    b = _room("B", 4, 0, floor=1)
    assert _rooms_adjacent(a, b) is False


# ── Scoring over a graph ──────────────────────────────────────────────────────


def _two_node_graph(strength="MUST"):
    graph = ProgramGraph()
    graph.add_node(Node(id="a", label="A", space_type="office"))
    graph.add_node(Node(id="b", label="B", space_type="office"))
    graph.add_edge(Edge(node_a="a", node_b="b", relation_type="adjacent", strength=strength))
    return graph


def test_satisfied_must_scores_one():
    graph = _two_node_graph("MUST")
    layout = {"rooms": [_room("A", 0, 0), _room("B", 4, 0)]}
    sat = score_graph_satisfaction(graph, layout)
    assert sat.must_total == 1
    assert sat.must_satisfied == 1
    assert sat.score == 1.0
    assert sat.unsatisfied_must == []


def test_unsatisfied_must_scores_zero_and_is_reported():
    graph = _two_node_graph("MUST")
    layout = {"rooms": [_room("A", 0, 0), _room("B", 30, 0)]}
    sat = score_graph_satisfaction(graph, layout)
    assert sat.must_total == 1
    assert sat.must_satisfied == 0
    assert sat.score == 0.0
    assert sat.unsatisfied_must == ["A ↔ B"]


def test_no_constraints_scores_one():
    graph = ProgramGraph()
    graph.add_node(Node(id="a", label="A"))
    sat = score_graph_satisfaction(graph, {"rooms": [_room("A", 0, 0)]})
    assert sat.must_total == 0 and sat.should_total == 0
    assert sat.score == 1.0


def test_should_is_weighted_below_must():
    graph = _two_node_graph("SHOULD")
    layout = {"rooms": [_room("A", 0, 0), _room("B", 30, 0)]}  # unmet SHOULD
    sat = score_graph_satisfaction(graph, layout)
    assert sat.should_total == 1 and sat.should_satisfied == 0
    assert sat.score == 0.0


# ── Integration: score a really generated layout ─────────────────────────────


@pytest.mark.parametrize("prompt", [
    "a clinic where the reception is next to the waiting room and a consultation room next to the bathroom",
    "2 bedroom apartment where the kitchen is next to the dining room and the living room next to the kitchen",
    "an office where the workspace is next to the reception",
])
def test_scores_a_generated_layout(prompt):
    parsed = parse_prompt(prompt)
    specs = parsed_to_room_specs(parsed)
    graph = from_parser_output(parsed, specs)
    layout = generate_layout(
        specs,
        prompt=prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    sat = score_graph_satisfaction(graph, layout)
    # There are real MUST adjacencies to measure, and the score is a valid ratio.
    assert sat.must_total >= 1
    assert 0.0 <= sat.score <= 1.0
    assert sat.must_satisfied <= sat.must_total
    assert isinstance(sat.as_dict()["unsatisfiedMust"], list)
