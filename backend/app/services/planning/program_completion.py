"""Program completion rules — graph mutators that fill in structural
necessities a raw program didn't specify. Phase 2.2b's replacement for
``layout_engine/engine.py``'s old inline auto-entry hack
(``counts[RoomType.entry] = 1``).

Two rules exist: every program gets exactly one entry/foyer node if it has
none (mirrors the old hack's residential behavior exactly), and — Phase 4 of
the engine generalization workflow — a corridor node when there are enough
private/semi-private rooms to need one and none already exists. Building-
type-aware completion (reception for a clinic, lobby for an office, a
loading-dock-adjacent entry for a warehouse) stays unstarted.
"""
from app.config.mvp_defaults import ROOM_SIZING
from app.schemas.requirements import RoomType
from app.services.planning.program_graph import Edge, Node, ProgramGraph, add_requirements_node

# A program may carry either spelling depending on where its nodes came from:
# "entry" (raw RoomType.value, from_requirements' spec.rooms branch — the one
# engine.py actually runs today) or "foyer" (the catalog-canonical key, from
# spec.spaces or the other adapters). Both count as "already has an entry".
_ENTRY_SYNONYMS = ("entry", "foyer")


def ensure_entry(graph: ProgramGraph) -> ProgramGraph:
    """Inject a single entry node if the program has none. Every house needs
    a way in — mirrors ``ROOM_SIZING[RoomType.entry]`` exactly so residential
    generation is unaffected by this rule existing. The injected node uses
    the raw "entry" spelling, matching what `from_requirements` itself emits
    for RoomType-sourced programs (see its module docstring)."""
    if any(graph.nodes_of_space_type(t) for t in _ENTRY_SYNONYMS):
        return graph
    sizing = ROOM_SIZING[RoomType.entry]
    add_requirements_node(
        graph, {}, "entry",
        label="Entry",
        target_area_sqm=sizing.preferred_area_m2,
        min_width_m=sizing.min_w,
        min_depth_m=sizing.min_d,
    )
    return graph


# The doc's own literal condition ("no circulation node") would use
# node.type == "circulation" — but that set (program_graph.py's
# _CIRCULATION_TYPES) also includes entry/foyer/lobby/staircase, and
# ensure_entry has *always* already run by the time this rule does (see
# engine.py::_build_program's `ensure_corridor(ensure_entry(...))` chaining),
# so a broad check would see the just-injected entry and never fire — the
# exact same false-positive already caught and fixed for the archetype
# selector's "circulation node" gate (Phase 3.2). A corridor node is
# specifically a spine/hallway type, not any circulation node.
_CORRIDOR_SYNONYMS = ("corridor", "hallway", "passage", "passageway")
_CORRIDOR_TRIGGER_ZONES = ("private", "semi_private")
# The doc's own Phase 4.1 prose says ">= 3"; lowered to 2 after wiring this
# rule in and running it against the Phase 4.5 privacy-chain hard check
# (through_room_access) — 2 genuinely private rooms with no other neighbour
# is already enough to landlock one behind the other (a real, derandomized
# Hypothesis counterexample: a lone pooja_room whose only neighbours were a
# bedroom and a bathroom). This also matches the threshold the pre-existing
# `planning/validation.py` "no circulation" warning already used
# (`private_count >= 2`), which the doc cites as this rule's own precedent —
# the doc's literal "3" was the outlier, not this value.
_MIN_ROOMS_NEEDING_CORRIDOR = 2


def ensure_corridor(graph: ProgramGraph) -> ProgramGraph:
    """Inject a single corridor node when the program has enough private/
    semi-private rooms to need real circulation and doesn't already have one
    (workflow Phase 4.1). Sizing comes from ``catalog.get("corridor")`` —
    the residential-context ``min_w`` (see ``space_catalog.CIRCULATION_WIDTHS``)
    — so the corridor is a real, catalog-backed room, not an ad-hoc size."""
    from app.services import catalog  # local: avoid a module-load-time cycle
    # with catalog (mirrors to_engine_program's own local import for the
    # same reason — see that function's docstring).

    if any(graph.nodes_of_space_type(t) for t in _CORRIDOR_SYNONYMS):
        return graph
    trigger_count = sum(1 for n in graph.nodes if n.zone in _CORRIDOR_TRIGGER_ZONES)
    if trigger_count < _MIN_ROOMS_NEEDING_CORRIDOR:
        return graph

    space = catalog.get("corridor")
    add_requirements_node(
        graph, {}, "corridor",
        label="Corridor",
        target_area_sqm=space.preferred_area_m2,
        min_width_m=space.min_w,
        min_depth_m=space.min_d,
    )
    return graph


_STAIR_TYPES = ("staircase", "stairs")
_LIFT_TYPES = ("lift", "elevator")
_LANDING_TYPES = ("corridor", "hallway")


def _ensure_one_per_floor(
    graph: ProgramGraph,
    aliases: tuple[str, ...],
    floors: int,
    *,
    canonical_type: str,
    label: str,
    min_width_m: float,
    min_depth_m: float,
) -> list[Node]:
    existing = [node for node in graph.nodes if node.space_type in aliases]
    by_floor = {
        node.floor_index: node
        for node in existing
        if node.floor_index is not None and 0 <= node.floor_index < floors
    }
    unpinned = [node for node in existing if node.floor_index is None]
    result: list[Node] = []
    for floor in range(floors):
        node = by_floor.get(floor)
        if node is None and unpinned:
            node = unpinned.pop(0)
            node.floor_index = floor
        if node is None:
            node = graph.add_node(Node(
                type="circulation",
                space_type=canonical_type,
                label=f"{label} {floor + 1}",
                zone="circulation",
                target_area_sqm=round(min_width_m * min_depth_m, 2),
                min_width_m=min_width_m,
                min_depth_m=min_depth_m,
                floor_index=floor,
                source="inferred_rule",
            ))
        else:
            # A REUSED node (user-requested stair/lift, or a corridor injected
            # by `ensure_corridor`) keeps its own catalog sizing, which does
            # not have to equal the sizing injected nodes get here — a
            # user-supplied `staircase` is 2.4x1.2 while the commercial
            # injected one is 2.4x1.5, and `lift` is only ensured per floor
            # under the rule below. `archetypes.vertical_core_bands` derives
            # the core footprint from ITS OWN floor's node, so a mismatch
            # makes floor N's core a different size from floor N+1's — which
            # is a `staircase_alignment` hard violation AND (because
            # `hard_constraints._door_adjacency` only links stairs with an
            # identical footprint) leaves every upper floor unreachable.
            # Normalizing here is what makes "one aligned core per floor"
            # true by construction rather than by luck of provenance.
            node.min_width_m = min_width_m
            node.min_depth_m = min_depth_m
        result.append(node)
    return result


def _ensure_stacked_edges(graph: ProgramGraph, nodes: list[Node], label: str) -> None:
    existing = {
        (edge.node_a, edge.node_b, edge.relation_type)
        for edge in graph.edges
    }
    for lower, upper in zip(nodes, nodes[1:]):
        key = (lower.id, upper.id, "stacked_above")
        reverse = (upper.id, lower.id, "stacked_above")
        if key in existing or reverse in existing:
            continue
        graph.add_edge(Edge(
            node_a=lower.id,
            node_b=upper.id,
            relation_type="stacked_above",
            strength="MUST",
            reason=f"{label} must align across consecutive floors",
        ))
        existing.add(key)


def ensure_vertical_circulation(
    graph: ProgramGraph,
    floors: int,
    *,
    commercial: bool = False,
    accessibility: bool = False,
) -> ProgramGraph:
    """Add one pinned stair and landing per floor, plus a lift when required.

    Existing unpinned nodes are reused before anything is injected. Repeated
    calls are idempotent. Stacked-above edges deliberately stay out of the
    floor assignment's same-floor MUST components.
    """
    if floors < 1:
        raise ValueError("floors must be at least 1")
    if floors == 1:
        return graph

    stair_width = 1.5 if commercial else 1.2
    stairs = _ensure_one_per_floor(
        graph,
        _STAIR_TYPES,
        floors,
        canonical_type="staircase",
        label="Staircase",
        min_width_m=2.4,
        min_depth_m=stair_width,
    )
    _ensure_stacked_edges(graph, stairs, "staircase")

    # Every level needs a circulation root; upper floors cannot route from
    # the ground-floor corridor or entry.
    _ensure_one_per_floor(
        graph,
        _LANDING_TYPES,
        floors,
        canonical_type="corridor",
        label="Landing",
        min_width_m=stair_width,
        min_depth_m=1.5,
    )

    # A lift the program ALREADY asks for must also become a per-floor aligned
    # core: leaving a single lift node unpinned lets `assign_floors` drop it on
    # one floor only, and `vertical_core_bands` widens that floor's core to the
    # lift while every other floor's core stays stair-width — the same
    # misalignment `_ensure_one_per_floor` normalizes dimensions against above.
    has_lift = any(node.space_type in _LIFT_TYPES for node in graph.nodes)
    if floors >= 3 or accessibility or has_lift:
        lifts = _ensure_one_per_floor(
            graph,
            _LIFT_TYPES,
            floors,
            canonical_type="lift",
            label="Lift",
            min_width_m=1.8,
            min_depth_m=1.8,
        )
        _ensure_stacked_edges(graph, lifts, "lift")
    return graph
