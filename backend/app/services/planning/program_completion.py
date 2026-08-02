"""Program completion rules — graph mutators that fill in structural
necessities a raw program didn't specify. Phase 2.2b's replacement for
``layout_engine/engine.py``'s old inline auto-entry hack
(``counts[RoomType.entry] = 1``).

Only one rule exists today, and it exactly mirrors that hack's residential
behavior: every program gets exactly one entry/foyer node if it has none.
Building-type-aware completion (reception for a clinic, lobby for an office,
a loading-dock-adjacent entry for a warehouse) is Phase 4 (circulation)
work — this module is the seam, not yet the generalization.
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
