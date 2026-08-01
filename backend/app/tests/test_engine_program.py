"""Phase 2.1 — EngineProgram bridge. Purely additive: engine.py does not
consume this yet (Phase 2.2), so these tests only pin the bridge itself."""
from app.services.layout_engine.subdivision import RoomNeed
from app.services.planning import Edge, Node, ProgramGraph, to_engine_program
from app.services.planning.program_graph import from_room_specs
from app.services.prompt_service import RoomSpec


def test_needs_are_room_need_instances_keyed_by_node_id():
    graph = from_room_specs([
        RoomSpec(label="Bedroom 1", room_type="bedroom", w=4, h=3, d=4),
    ])
    program = to_engine_program(graph)
    assert len(program.needs) == 1
    need = program.needs[0]
    assert isinstance(need, RoomNeed)
    assert need.key == graph.nodes[0].id
    assert need.type == "bedroom"


# ── Sizing precedence: explicit > size_hint x multiplier > catalog > derived ─


def test_explicit_target_area_wins_over_everything():
    node = Node(id="a", space_type="bedroom", target_area_sqm=20.0, size_hint="small")
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert program.needs[0].preferred_area == 20.0


def test_size_hint_scales_the_catalog_default_when_no_explicit_area():
    from app.services.catalog import get as catalog_get

    catalog_default = catalog_get("bedroom").preferred_area_m2
    node = Node(id="a", space_type="bedroom", size_hint="large")
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert program.needs[0].preferred_area == round(catalog_default * 1.35, 2)


def test_catalog_default_used_when_no_explicit_area_and_no_size_hint():
    from app.services.catalog import get as catalog_get

    node = Node(id="a", space_type="bedroom")
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert program.needs[0].preferred_area == catalog_get("bedroom").preferred_area_m2


def test_unknown_space_type_falls_back_to_width_times_depth():
    node = Node(id="a", space_type="recording_studio", width=5.0, depth=4.0)
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert program.needs[0].preferred_area == 20.0
    assert program.needs[0].min_w == 1.2
    assert program.needs[0].min_d == 1.2


def test_hard_minima_never_scale_with_size_hint():
    # bathroom: catalog min_w/min_d = 1.5 x 2.1 (from ROOM_SIZING) — a "large"
    # hint must not inflate the hard minimum, only the preferred area.
    node = Node(id="a", space_type="bathroom", size_hint="large")
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert (program.needs[0].min_w, program.needs[0].min_d) == (1.5, 2.1)


def test_explicit_node_minima_override_the_catalog():
    node = Node(id="a", space_type="bedroom", min_width_m=5.0, min_depth_m=6.0)
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert (program.needs[0].min_w, program.needs[0].min_d) == (5.0, 6.0)


# ── Id-level (not type-level) adjacency ──────────────────────────────────────


def test_must_avoid_are_id_level_so_each_same_type_instance_keeps_its_own_pairs():
    bed1 = Node(id="bed1", space_type="bedroom")
    bed2 = Node(id="bed2", space_type="bedroom")
    bath = Node(id="bath1", space_type="bathroom")
    graph = ProgramGraph(nodes=[bed1, bed2, bath], edges=[
        Edge(node_a="bed1", node_b="bath1", relation_type="adjacent", strength="MUST"),
        Edge(node_a="bed2", node_b="bath1", relation_type="adjacent", strength="AVOID"),
    ])
    program = to_engine_program(graph)
    assert ("bed1", "bath1") in program.must_adjacent
    assert ("bed2", "bath1") not in program.must_adjacent
    assert ("bed2", "bath1") in program.avoid
    assert ("bed1", "bath1") not in program.avoid


def test_should_strength_buckets_separately_from_must():
    graph = ProgramGraph(nodes=[Node(id="a"), Node(id="b")], edges=[
        Edge(node_a="a", node_b="b", relation_type="adjacent", strength="SHOULD"),
    ])
    program = to_engine_program(graph)
    assert program.should_adjacent == [("a", "b")]
    assert program.must_adjacent == []


def test_separated_relation_type_is_an_avoid_regardless_of_strength():
    graph = ProgramGraph(nodes=[Node(id="a"), Node(id="b")], edges=[
        Edge(node_a="a", node_b="b", relation_type="separated", strength="MUST"),
    ])
    program = to_engine_program(graph)
    assert program.avoid == [("a", "b")]
    assert program.must_adjacent == []


# ── zone_of / floor_of / circulation_nodes / entry_node ──────────────────────


def test_zone_of_and_floor_of_cover_every_buildable_node():
    graph = from_room_specs([
        RoomSpec(label="Bedroom", room_type="bedroom", w=4, h=3, d=4),
        RoomSpec(label="Corridor", room_type="corridor", w=6, h=3, d=1.5),
    ])
    program = to_engine_program(graph)
    ids = {n.id for n in graph.nodes}
    assert set(program.zone_of) == ids
    assert set(program.floor_of) == ids


def test_floor_of_resolves_from_floor_preference():
    node = Node(id="a", space_type="bedroom", floor_preference="upper")
    graph = ProgramGraph(nodes=[node])
    program = to_engine_program(graph)
    assert program.floor_of["a"] == 1


def test_circulation_nodes_are_the_buildable_circulation_typed_nodes():
    graph = from_room_specs([
        RoomSpec(label="Bedroom", room_type="bedroom", w=4, h=3, d=4),
        RoomSpec(label="Corridor", room_type="corridor", w=6, h=3, d=1.5),
    ])
    program = to_engine_program(graph)
    corridor_id = graph.first_of_space_type("corridor").id
    assert program.circulation_nodes == [corridor_id]


def test_entry_node_prefers_entry_type_over_other_circulation_types():
    graph = from_room_specs([
        RoomSpec(label="Lobby", room_type="lobby", w=4, h=3, d=4),
        RoomSpec(label="Entry", room_type="entry", w=2, h=3, d=2),
    ])
    program = to_engine_program(graph)
    entry_id = graph.first_of_space_type("entry").id
    assert program.entry_node == entry_id


def test_entry_node_is_none_when_no_entry_like_node_exists():
    graph = from_room_specs([RoomSpec(label="Bedroom", room_type="bedroom", w=4, h=3, d=4)])
    program = to_engine_program(graph)
    assert program.entry_node is None


def test_buildable_nodes_only_openings_and_structural_excluded():
    graph = ProgramGraph(nodes=[
        Node(id="a", type="space", space_type="bedroom"),
        Node(id="b", type="opening", space_type="window"),
        Node(id="c", type="structural", space_type="column"),
    ])
    program = to_engine_program(graph)
    assert [n.key for n in program.needs] == ["a"]
