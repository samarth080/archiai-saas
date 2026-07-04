"""Phase 4 Stages 1 + 3 — prepare (edge unification) and MUST-cluster contraction."""
from app.services.layout_pattern_service import fallback_layout_rules
from app.services.planning.clustering import contract
from app.services.planning.graph_layout import prepare
from app.services.planning.program_graph import Edge, Node, ProgramGraph
from app.services.prompt_service import parse_prompt, parsed_to_room_specs
from app.services.planning import from_parser_output


def _clinic_graph():
    parsed = parse_prompt(
        "clinic where the reception is next to the waiting room and a consultation room next to the bathroom"
    )
    specs = parsed_to_room_specs(parsed)
    return from_parser_output(parsed, specs), parsed


# ── prepare (Stage 1) ─────────────────────────────────────────────────────────


def test_prepare_fills_numeric_fields_and_is_deterministic():
    graph, _ = _clinic_graph()
    rules = fallback_layout_rules("clinic", {n.space_type for n in graph.nodes})
    first = prepare(graph, rules)
    second = prepare(graph, rules)
    assert first == second  # frozen dataclasses → structural equality
    assert all(n.area > 0 and n.min_w >= 1.5 and n.min_d >= 1.5 for n in first.nodes)


def test_prepare_maps_must_edges():
    graph, _ = _clinic_graph()
    prepared = prepare(graph, None)
    assert any(e.relation == "must" for e in prepared.edges)


def test_prepare_pattern_rules_add_should_edges():
    graph, _ = _clinic_graph()
    without = prepare(graph, None)
    rules = fallback_layout_rules("clinic", {n.space_type for n in graph.nodes})
    with_rules = prepare(graph, rules)
    # pattern-rule adjacencies add edges the bare graph didn't have
    assert len(with_rules.edges) >= len(without.edges)
    assert any(e.relation == "should" for e in with_rules.edges)


def test_prepare_must_over_avoid_conflict_warns():
    graph = ProgramGraph()
    graph.add_node(Node(id="k", space_type="kitchen", label="Kitchen", zone="service", width=4, depth=4, height=3))
    graph.add_node(Node(id="b", space_type="bedroom", label="Bedroom", zone="private", width=4, depth=4, height=3))
    # explicit MUST adjacency between kitchen & bedroom, which pattern rules say to AVOID
    graph.add_edge(Edge(node_a="k", node_b="b", relation_type="adjacent", strength="MUST"))
    rules = fallback_layout_rules("house", {"kitchen", "bedroom"})

    prepared = prepare(graph, rules)
    pair = next(e for e in prepared.edges if {e.a, e.b} == {"k", "b"})
    assert pair.relation == "must"  # MUST wins
    assert any("Conflicting rules" in w for w in prepared.warnings)


# ── clustering (Stage 3) ──────────────────────────────────────────────────────


def test_must_pair_forms_one_cluster():
    graph, _ = _clinic_graph()
    prepared = prepare(graph, None)
    cg = contract(prepared)

    # reception & waiting_room are MUST-adjacent → same cluster
    reception = next(n.id for n in prepared.nodes if n.space_type == "reception")
    waiting = next(n.id for n in prepared.nodes if n.space_type == "waiting_room")
    cluster_of = {m.id: c.id for c in cg.clusters for m in c.members}
    assert cluster_of[reception] == cluster_of[waiting]
    # that cluster has ≥ 2 members
    assert len(cg.cluster(cluster_of[reception]).members) >= 2


def test_singletons_become_one_member_clusters():
    graph = ProgramGraph()
    graph.add_node(Node(id="a", space_type="office", label="Office", zone="private", width=4, depth=4, height=3))
    graph.add_node(Node(id="b", space_type="storage", label="Storage", zone="service", width=3, depth=3, height=3))
    cg = contract(prepare(graph, None))
    assert len(cg.clusters) == 2
    assert all(len(c.members) == 1 for c in cg.clusters)


def test_contract_is_deterministic_and_covers_all_nodes():
    graph, _ = _clinic_graph()
    prepared = prepare(graph, fallback_layout_rules("clinic", {n.space_type for n in graph.nodes}))
    a = contract(prepared)
    b = contract(prepared)
    assert a == b
    members = sum(len(c.members) for c in a.clusters)
    assert members == len(prepared.nodes)  # every node lands in exactly one cluster


def test_cluster_item_aggregates_area_and_external():
    graph, _ = _clinic_graph()
    cg = contract(prepare(graph, None))
    cluster = max(cg.clusters, key=lambda c: len(c.members))
    item = cluster.item()
    assert item.area == sum(m.area for m in cluster.members)
    assert item.needs_external == any(m.needs_external for m in cluster.members)
