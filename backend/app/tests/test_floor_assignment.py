"""Engine-generalization Phase 7 floor-assignment foundation."""

import pytest

from app.services.planning import Edge, Node, ProgramGraph, assign_floors


def _graph(*nodes: Node, edges: list[Edge] | None = None) -> ProgramGraph:
    return ProgramGraph(nodes=list(nodes), edges=edges or [])


def test_single_floor_keeps_every_node_on_ground():
    graph = _graph(
        Node(id="entry", space_type="entry", target_area_sqm=3),
        Node(id="bed", space_type="bedroom", target_area_sqm=12),
    )

    result = assign_floors(graph, 1)

    assert result.floor_of == {"bed": 0, "entry": 0}


def test_explicit_and_type_derived_day_night_preferences_are_honoured():
    graph = _graph(
        Node(id="reception", space_type="reception", target_area_sqm=10),
        Node(id="bed", space_type="bedroom", target_area_sqm=12),
        Node(
            id="office",
            space_type="office",
            floor_preference="upper",
            target_area_sqm=8,
        ),
    )

    result = assign_floors(graph, 2)

    assert result.floor_of == {"bed": 1, "office": 1, "reception": 0}


def test_unpinned_components_balance_largest_first_deterministically():
    graph = _graph(
        Node(id="a", space_type="storage", target_area_sqm=10),
        Node(id="b", space_type="storage", target_area_sqm=8),
        Node(id="c", space_type="storage", target_area_sqm=6),
        Node(id="d", space_type="storage", target_area_sqm=4),
    )

    first = assign_floors(graph, 2)
    second = assign_floors(graph, 2)

    assert first == second
    assert first.floor_of == {"a": 0, "b": 1, "c": 1, "d": 0}


def test_must_adjacent_nodes_never_split_and_lighter_preference_is_moved():
    graph = _graph(
        Node(
            id="public",
            space_type="lobby",
            floor_preference="ground",
            target_area_sqm=20,
        ),
        Node(
            id="private",
            space_type="private_office",
            floor_preference="upper",
            target_area_sqm=5,
        ),
        edges=[
            Edge(
                node_a="public",
                node_b="private",
                relation_type="adjacent",
                strength="MUST",
            ),
        ],
    )

    result = assign_floors(graph, 2)

    assert result.floor_of["public"] == result.floor_of["private"] == 0
    assert "moving the lighter side" in result.reasons[0].reason


def test_stacked_above_is_not_collapsed_into_one_floor():
    graph = _graph(
        Node(
            id="stair-ground",
            space_type="staircase",
            floor_preference="ground",
            target_area_sqm=3,
        ),
        Node(
            id="stair-upper",
            space_type="staircase",
            floor_preference="upper",
            target_area_sqm=3,
        ),
        edges=[
            Edge(
                node_a="stair-ground",
                node_b="stair-upper",
                relation_type="stacked_above",
                strength="MUST",
            ),
        ],
    )

    result = assign_floors(graph, 2)

    assert result.floor_of == {"stair-ground": 0, "stair-upper": 1}


def test_rejects_an_impossible_floor_count():
    with pytest.raises(ValueError, match="at least 1"):
        assign_floors(ProgramGraph(), 0)
