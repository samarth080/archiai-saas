# Non-ML Graph Layout Engine — ProgramGraph

ArchiAI's layout engine is **deterministic and explainable** — no ML, no neural
nets, no paid AI APIs. Generation is rule/constraint/graph/search-based. This
document describes the `ProgramGraph` abstraction (Sprint 17 Phase 2,
`backend/app/services/planning/`) that the later graph-driven planning phases
build on.

## Why no ML

- **Explainability**: every placement decision traces to a rule or constraint we
  can show the user ("bedroom placed on the private row because zone=private").
- **Determinism**: the same brief always yields the same candidates — testable,
  debuggable, reproducible.
- **No data/β dependency**: works offline with zero training data or API keys.

Graph2Plan and Hypar are inspiration for the *representation* (typed nodes,
relative-position edges, boundary/front-door modelling) — we deliberately do
**not** port any GNN or learned solver.

## The abstraction

A building is a graph of typed **nodes** connected by relationship **edges**,
independent of any residential vocabulary — a house, office, clinic, and
warehouse are all expressed the same way.

### Node

Building-type-agnostic. `type ∈ {space, circulation, service, object,
furniture, structural, opening}`; `space_type` is a free string
(`bedroom, office, consultation_room, retail_area, lab, corridor, …`). Carries
area/dimension targets, `zone` (public / private / semi_private / service /
circulation / outdoor / technical), privacy, daylight/acoustic need, and flags
(`wet_room`, `requires_external_wall`, `can_be_open_plan`, `staff_only`, …).
All fields default so partial construction is always safe.

### Edge

`relation_type ∈ {adjacent, near, separated, connected_by_door,
visual_connection, service_dependency, circulation_path, stacked_above,
aligned_with}`, `strength ∈ {MUST, SHOULD, AVOID}`, plus
`preferred_relative_position`, `min_shared_wall_m`, `door_required`, and a
human-readable `reason`.

### Constraint families the graph can express

Adjacency; separation/privacy; public→private progression; entry/lobby/
circulation logic; wet-room/service clustering; daylight/window need; corridor
reachability; accessibility & minimum clearance; door placement/clearance;
stairs/lift & vertical circulation; furniture clearance; aspect-ratio limits;
no-overlap; inside-footprint; plot/boundary; export-readiness.

## Adapters and the RoomSpec bridge

The graph is **additive** — it sits alongside the existing
`parse_prompt → RoomSpec → generate_layout` path and never changes a generated
layout today.

- `from_parser_output(parsed, room_specs)` — build a graph from the NLU parser.
- `from_building_template(template)` — build from a building template.
- `from_user_objects(canvas_objects)` — build from the editor's rooms.
- `merge(a, b)` — combine graphs (id-collision-safe).
- **Bridge**: `to_room_specs(graph)` / `from_room_specs(specs)`.

`to_room_specs(from_parser_output(parsed, specs)) == specs`, so
`generate_layout` produces byte-identical output (ids aside) whether it is fed
RoomSpecs directly or via the graph. This is pinned by golden tests across
apartment / house / office / clinic / warehouse / restaurant programs
(`backend/app/tests/test_program_graph.py`).

## Validation

`validate(graph)` returns explainable, non-raising warnings (generation still
proceeds): missing edge node, public↔private MUST-adjacency, external-wall /
daylight pressure, missing circulation for multiple private spaces, and
undersized spaces. Messages are written for a human, e.g. *"2 private spaces but
no corridor/hallway — they may only be reachable through each other."*

## Roadmap

Phase 2 delivered the representation + bridge + validation. Later phases consume
it: graph-driven BSP placement scored by constraint satisfaction (Phase 4), a
real circulation graph + doors on shared walls (Phase 5), deterministic
furniture templates (Phase 6). None of these require ML.
