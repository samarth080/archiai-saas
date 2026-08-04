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
from app.services.planning.program_graph import ProgramGraph, add_requirements_node

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
_MIN_ROOMS_NEEDING_CORRIDOR = 3  # workflow Phase 4.1: "private ∪ semi_private >= 3"


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
