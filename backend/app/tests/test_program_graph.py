"""ProgramGraph (Phase 2) — bridge losslessness, validation, agnosticism."""
import pytest

from app.services.building_template_service import get_building_template
from app.services.layout_service import generate_layout
from app.services.planning import (
    Edge,
    Node,
    ProgramGraph,
    from_building_template,
    from_parser_output,
    from_room_specs,
    from_user_objects,
    merge,
    to_room_specs,
    validate,
)
from app.services.planning.validation import (
    CODE_MISSING_ADJACENCY_NODE,
    CODE_NO_CIRCULATION,
    CODE_UNDERSIZED,
)
from app.services.prompt_service import RoomSpec, parse_prompt, parsed_to_room_specs


def _strip_ids(obj):
    """Drop uuid-ish keys so two generation runs can be compared structurally."""
    if isinstance(obj, dict):
        return {k: _strip_ids(v) for k, v in obj.items() if k not in ("id",)}
    if isinstance(obj, list):
        return [_strip_ids(x) for x in obj]
    return obj


# ── Golden: bridge is lossless and produces identical layouts ────────────────

GOLDEN_PROMPTS = [
    "2 bedroom apartment with kitchen and living room",
    "3 bedroom house with 2 bathrooms, kitchen, dining room and a study",
    "small office with a reception, 3 meeting rooms and an open workspace",
    "a clinic with reception, waiting room and 2 consultation rooms",
    "warehouse with storage and a small office",
    "a restaurant with a dining area, kitchen and 2 bathrooms",
]


@pytest.mark.parametrize("prompt", GOLDEN_PROMPTS)
def test_bridge_round_trips_room_specs(prompt):
    parsed = parse_prompt(prompt)
    specs = parsed_to_room_specs(parsed)
    bridged = to_room_specs(from_parser_output(parsed, specs))
    assert bridged == specs


@pytest.mark.parametrize("prompt", GOLDEN_PROMPTS)
def test_graph_derived_specs_generate_identical_layout(prompt):
    parsed = parse_prompt(prompt)
    specs = parsed_to_room_specs(parsed)
    bridged = to_room_specs(from_parser_output(parsed, specs))

    kwargs = dict(
        prompt=prompt,
        building_type=parsed.building_type,
        total_floors=parsed.total_floors,
        adjacency_constraints=parsed.adjacency_constraints,
        zone_assignments=parsed.zone_assignments,
    )
    direct = generate_layout(specs, **kwargs)
    via_graph = generate_layout(bridged, **kwargs)
    assert _strip_ids(direct) == _strip_ids(via_graph)


# ── Building-type-agnostic ────────────────────────────────────────────────────


def test_graph_classifies_across_building_types():
    specs = [
        RoomSpec(label="Reception", room_type="reception", w=4, h=3, d=4),
        RoomSpec(label="Consultation Room", room_type="consultation_room", w=3.5, h=3, d=3.5),
        RoomSpec(label="Storage", room_type="storage", w=3, h=3, d=3),
        RoomSpec(label="Corridor", room_type="corridor", w=6, h=3, d=1.5),
    ]
    graph = from_room_specs(specs)
    kinds = {n.space_type: n.type for n in graph.nodes}
    assert kinds["storage"] == "service"
    assert kinds["corridor"] == "circulation"
    assert kinds["consultation_room"] == "space"
    # Round-trips regardless of vocabulary.
    assert to_room_specs(graph) == specs


def test_warehouse_program_is_buildable():
    parsed = parse_prompt("warehouse with storage and a small office")
    specs = parsed_to_room_specs(parsed)
    graph = from_parser_output(parsed, specs)
    assert len(graph.buildable_nodes()) == len(specs)


# ── Adapters ─────────────────────────────────────────────────────────────────


def test_from_building_template_builds_nodes_and_edges():
    template = get_building_template("apartment")
    graph = from_building_template(template)
    assert len(graph.buildable_nodes()) >= len(template.default_rooms)
    assert all(n.source == "template" for n in graph.nodes)
    # Bridging a template graph yields usable specs.
    specs = to_room_specs(graph)
    assert specs and all(s.w > 0 and s.d > 0 for s in specs)


def test_from_user_objects_reads_canvas_rooms():
    objects = [
        {"id": "a", "label": "Lab", "objectType": "room", "roomType": "office",
         "size": {"w": 5, "h": 3, "d": 4}},
        {"id": "b", "label": "WC", "objectType": "room", "roomType": "bathroom",
         "size": {"w": 2, "h": 3, "d": 2}},
    ]
    graph = from_user_objects(objects)
    assert [n.id for n in graph.nodes] == ["a", "b"]
    assert graph.get_node("b").wet_room is True
    assert graph.get_node("b").source == "user_added"


def test_merge_rebases_colliding_ids_and_keeps_all_nodes():
    a = from_user_objects([{"id": "x", "roomType": "office", "size": {"w": 4, "h": 3, "d": 4}}])
    b = from_user_objects([{"id": "x", "roomType": "storage", "size": {"w": 3, "h": 3, "d": 3}}])
    merged = merge(a, b)
    assert len(merged.nodes) == 2
    assert len({n.id for n in merged.nodes}) == 2  # id collision was re-based


def test_merge_rebase_does_not_reuse_the_id_it_is_replacing():
    """The generated replacement was `node-{len(merged.nodes)}`, which lands
    on the colliding id itself whenever the base's own ids are sparse
    (["node-0", "node-2"] + an incoming "node-2" -> len is 2 -> "node-2").
    That appended a second "node-2", so get_node and every edge resolved to
    only one of them — a silent drop of exactly the kind merge promises not
    to do."""
    base = ProgramGraph(nodes=[Node(id="node-0", label="A"), Node(id="node-2", label="B")])
    other = ProgramGraph(
        nodes=[Node(id="node-2", label="C")],
        edges=[Edge(node_a="node-2", node_b="node-0")],
    )

    merged = merge(base, other)

    ids = [n.id for n in merged.nodes]
    assert len(ids) == len(set(ids)) == 3
    assert {n.label for n in merged.nodes} == {"A", "B", "C"}
    # the re-based edge points at the incoming node, not the base's namesake
    assert merged.get_node(merged.edges[0].node_a).label == "C"


# ── Validation ────────────────────────────────────────────────────────────────


def test_validate_flags_missing_edge_node():
    graph = ProgramGraph()
    graph.add_node(Node(id="real", space_type="office", width=4, depth=4))
    graph.add_edge(Edge(node_a="real", node_b="ghost", strength="MUST"))
    codes = {w.code for w in validate(graph)}
    assert CODE_MISSING_ADJACENCY_NODE in codes


def test_validate_flags_missing_circulation():
    graph = from_room_specs([
        RoomSpec(label="Bedroom 1", room_type="bedroom", w=4, h=3, d=4),
        RoomSpec(label="Bedroom 2", room_type="bedroom", w=4, h=3, d=4),
    ])
    codes = {w.code for w in validate(graph)}
    assert CODE_NO_CIRCULATION in codes


def test_validate_flags_undersized_space():
    graph = from_room_specs([RoomSpec(label="Nook", room_type="office", w=0.8, h=3, d=3)])
    codes = {w.code for w in validate(graph)}
    assert CODE_UNDERSIZED in codes


def test_validate_returns_no_warnings_for_a_reasonable_program():
    parsed = parse_prompt("2 bedroom apartment with kitchen, living room, bathroom and a hallway")
    graph = from_parser_output(parsed, parsed_to_room_specs(parsed))
    warnings = validate(graph)
    # A hallway is present, so the missing-circulation warning must not fire.
    assert CODE_NO_CIRCULATION not in {w.code for w in warnings}
