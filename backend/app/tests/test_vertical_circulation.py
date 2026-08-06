"""Engine-generalization Phase 7 vertical-circulation completion."""

from app.services.planning import Node, ProgramGraph, assign_floors
from app.services.planning.program_completion import ensure_vertical_circulation


def _by_type(graph: ProgramGraph, *types: str) -> list[Node]:
    return [node for node in graph.nodes if node.space_type in types]


def test_single_floor_program_is_unchanged():
    graph = ProgramGraph(nodes=[Node(id="living", space_type="living_room")])

    assert ensure_vertical_circulation(graph, 1) is graph
    assert [node.id for node in graph.nodes] == ["living"]


def test_two_floors_get_pinned_stairs_and_landings_without_a_lift():
    graph = ensure_vertical_circulation(ProgramGraph(), 2)

    stairs = _by_type(graph, "staircase", "stairs")
    landings = _by_type(graph, "corridor", "hallway")
    assert [node.floor_index for node in stairs] == [0, 1]
    assert [node.floor_index for node in landings] == [0, 1]
    assert _by_type(graph, "lift", "elevator") == []
    assert any(
        edge.node_a == stairs[0].id
        and edge.node_b == stairs[1].id
        and edge.relation_type == "stacked_above"
        and edge.strength == "MUST"
        for edge in graph.edges
    )


def test_three_floors_get_one_aligned_lift_per_floor():
    graph = ensure_vertical_circulation(ProgramGraph(), 3)

    lifts = _by_type(graph, "lift", "elevator")
    assert [node.floor_index for node in lifts] == [0, 1, 2]
    lift_edges = [
        edge for edge in graph.edges
        if edge.relation_type == "stacked_above"
        and edge.node_a in {node.id for node in lifts}
    ]
    assert len(lift_edges) == 2


def test_accessibility_adds_a_lift_to_a_two_floor_program():
    graph = ensure_vertical_circulation(ProgramGraph(), 2, accessibility=True)

    assert [node.floor_index for node in _by_type(graph, "lift")] == [0, 1]


def test_existing_unpinned_stair_is_reused_and_completion_is_idempotent():
    existing = Node(id="user-stair", type="circulation", space_type="stairs")
    graph = ProgramGraph(nodes=[existing])

    ensure_vertical_circulation(graph, 2)
    first_counts = (len(graph.nodes), len(graph.edges))
    ensure_vertical_circulation(graph, 2)

    assert existing.floor_index == 0
    assert (len(graph.nodes), len(graph.edges)) == first_counts


def test_floor_assignment_honours_every_exact_core_floor():
    graph = ensure_vertical_circulation(ProgramGraph(), 3)

    assignment = assign_floors(graph, 3)

    assert all(
        assignment.floor_of[node.id] == node.floor_index
        for node in graph.nodes
    )
