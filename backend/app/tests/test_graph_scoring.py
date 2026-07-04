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


def test_room_on_perimeter_detects_boundary_vs_interior():
    from app.services.planning.graph_scoring import _room_on_perimeter

    footprint = {"x": 0.0, "z": 0.0, "w": 10.0, "d": 10.0}
    on_front = {"position": {"x": 2, "z": 2}, "size": {"w": 4, "d": 4}}  # z0 = 0
    interior = {"position": {"x": 5, "z": 5}, "size": {"w": 2, "d": 2}}  # x,z in [4,6]
    assert _room_on_perimeter(on_front, footprint) is True
    assert _room_on_perimeter(interior, footprint) is False


def test_daylight_flags_a_landlocked_room():
    from app.services.planning import from_room_specs
    from app.services.prompt_service import RoomSpec

    graph = from_room_specs([RoomSpec("Bedroom 1", "bedroom", 3, 3, 3)])
    assert graph.nodes[0].requires_external_wall is True  # sanity: bedroom needs daylight
    layout = {
        "rooms": [],
        "floors": [{
            "level": 0,
            "footprint": {"x": 0.0, "z": 0.0, "w": 10.0, "d": 10.0},
            "rooms": [{
                "label": "Bedroom 1", "floorLevel": 0,
                "position": {"x": 5, "y": 1.5, "z": 5}, "size": {"w": 2, "h": 3, "d": 2},
            }],
        }],
    }
    sat = score_graph_satisfaction(graph, layout)
    assert sat.daylight_total == 1
    assert sat.daylight_satisfied == 0
    assert sat.daylight_missing == ["Bedroom 1"]


def test_generator_avoids_landlocking_daylight_rooms():
    """A deep house program where the BSP candidate strands interior rooms — the
    daylight penalty steers the competition to a perimeter-friendly winner."""
    parsed = parse_prompt("3 bedroom house with living room, kitchen, 2 bathrooms and a study")
    specs = parsed_to_room_specs(parsed)
    layout = generate_layout(
        specs,
        prompt=parsed.raw_prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    sat = score_graph_satisfaction(from_parser_output(parsed, specs), layout)
    assert sat.daylight_total > 0
    assert sat.daylight_satisfied == sat.daylight_total  # winner strands no daylight room


def test_daylight_satisfied_when_on_perimeter():
    from app.services.planning import from_room_specs
    from app.services.prompt_service import RoomSpec

    graph = from_room_specs([RoomSpec("Bedroom 1", "bedroom", 4, 3, 4)])
    layout = {
        "rooms": [],
        "floors": [{
            "level": 0,
            "footprint": {"x": 0.0, "z": 0.0, "w": 10.0, "d": 10.0},
            "rooms": [{
                "label": "Bedroom 1", "floorLevel": 0,
                "position": {"x": 2, "y": 1.5, "z": 2}, "size": {"w": 4, "h": 3, "d": 4},
            }],
        }],
    }
    sat = score_graph_satisfaction(graph, layout)
    assert sat.daylight_total == 1
    assert sat.daylight_satisfied == 1
    assert sat.daylight_missing == []


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


# ── Graph-aware candidate selection (secondary key in generate_layout) ────────


def _typed_room(room_type, x, z, w=4.0, d=4.0, floor=0):
    return {
        "roomType": room_type,
        "floorLevel": floor,
        "position": {"x": x, "y": 1.5, "z": z},
        "size": {"w": w, "h": 3.0, "d": d},
    }


def test_candidate_adjacency_bonus_counts_realised_pairs():
    from app.services.layout_service import _candidate_adjacency_bonus

    must = {frozenset({"reception", "waiting_room"})}
    adjacent = {"rooms": [_typed_room("reception", 0, 0), _typed_room("waiting_room", 4, 0)]}
    far = {"rooms": [_typed_room("reception", 0, 0), _typed_room("waiting_room", 40, 0)]}

    assert _candidate_adjacency_bonus(adjacent, must, None) == 1.0
    assert _candidate_adjacency_bonus(far, must, None) == 0.0


def test_candidate_adjacency_bonus_weights_should_below_must():
    from app.services.layout_service import _candidate_adjacency_bonus

    should = {frozenset({"office", "meeting_room"})}
    adjacent = {"rooms": [_typed_room("office", 0, 0), _typed_room("meeting_room", 4, 0)]}
    assert _candidate_adjacency_bonus(adjacent, None, should) == pytest.approx(0.4)


def test_candidate_adjacency_bonus_zero_without_constraints():
    from app.services.layout_service import _candidate_adjacency_bonus

    cand = {"rooms": [_typed_room("office", 0, 0)]}
    assert _candidate_adjacency_bonus(cand, None, None) == 0.0


# ── Graph-driven candidate (Phase 4 slice 3) ─────────────────────────────────


def test_graph_candidate_realises_a_cross_zone_must_the_tiler_cannot():
    """A front room (reception) MUST-adjacent to a back room (consultation) can't
    share a wall in the zone tiler; the graph packer clusters them into one row,
    and the competing generator selects it."""
    from app.services.building_template_service import apply_template_defaults, get_building_template
    from app.services.layout_pattern_service import fallback_layout_rules
    from app.services.layout_service import (
        _build_layout_candidate,
        _candidate_must_satisfied,
        generate_layout,
    )

    prompt = "clinic where the reception is next to the consultation room"
    parsed = parse_prompt(prompt)
    must_pairs = {
        frozenset({c.room_a, c.room_b})
        for c in parsed.adjacency_constraints
        if c.strength == "MUST"
    }
    assert must_pairs, "test prompt must yield a MUST adjacency"

    specs = apply_template_defaults(parsed_to_room_specs(parsed), "clinic")
    rules = fallback_layout_rules("clinic", {s.room_type for s in specs})
    kw = dict(
        room_specs=specs, prompt=prompt, building_type="clinic", total_floors=1,
        pattern_rules=rules, total_area_sqm=None, template=get_building_template("clinic"),
        x_offset=0.0, must_adjacency_pairs=must_pairs,
    )
    tile = _build_layout_candidate(**kw, placement_style="tile")
    graph = _build_layout_candidate(**kw, placement_style="graph")
    assert _candidate_must_satisfied(graph, must_pairs) > _candidate_must_satisfied(tile, must_pairs)

    # End-to-end the competing generator selects the graph candidate here.
    layout = generate_layout(
        parsed_to_room_specs(parsed),
        prompt=prompt,
        building_type="clinic",
        total_floors=1,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    assert layout["metadata"]["placementEngine"] == "graph"
    # tile + bsp + graph (row-packer) + gtree (slicing tree) all compete on a MUST program
    assert layout["metadata"]["candidateCount"] == 4


def test_slicing_tree_wins_when_it_produces_the_best_layout():
    """The guillotine slicing tree ('gtree') competes alongside the row-packer
    and wins when its 2D partitioning yields the best layout — here it beats
    tile/BSP/row-packer while realising the MUST adjacency."""
    from app.services.layout_service import generate_layout

    prompt = "office where the workspace is next to the reception"
    parsed = parse_prompt(prompt)
    layout = generate_layout(
        parsed_to_room_specs(parsed),
        prompt=prompt,
        building_type="office",
        total_floors=1,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    assert layout["metadata"]["placementEngine"] == "gtree"


def test_graph_candidate_absent_without_must_constraints():
    """A SHOULD-only (or constraint-free) program keeps the 2-candidate tiler/BSP
    competition — no graph candidate is spawned."""
    from app.services.layout_service import generate_layout

    parsed = parse_prompt("apartment with living room, kitchen, dining room and bathroom")
    layout = generate_layout(
        parsed_to_room_specs(parsed),
        prompt=parsed.raw_prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    assert layout["metadata"]["candidateCount"] == 2
    assert layout["metadata"]["placementEngine"] in ("tile", "bsp")
