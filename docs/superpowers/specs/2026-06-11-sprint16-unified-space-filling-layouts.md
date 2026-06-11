# Sprint 16 — Unified Space-Filling Layouts & Adjacency Reasoning

**Branch:** `sprint-16/unified-space-filling-layouts` (off `main`)
**Date:** 2026-06-11
**Scope (approved):** Phases 1–3. Priority: **accurate room reasoning**.
**Out of scope this sprint:** quality-scorer space-utilization metric (Phase 4), 2D plan view / door openings / legend (Phase 5), any paid-AI or model-based generation.

---

## Problem statement

The generator has **two placement engines** in `backend/app/services/layout_service.py`:

1. **Tiled engine** (`_tile_rooms`) — residential types only (`_TILED_BUILDING_TYPES`). Rooms are
   scaled to share walls and fill an exact rectangle. No blank space. Good.
2. **Row-band engine** (`_place_rooms` + `_repair_rooms`) — everything else: office, clinic, retail,
   restaurant, school, classroom, and any prompt that resolves to a non-residential `building_type`.
   Each zone is placed as its own row beginning at `x_offset`, each with its own width. The building
   footprint is the bounding box of all rows, so a narrow single-room band leaves a large empty
   rectangle inside the boundary walls → the "ugly blank space."

Additional weaknesses (present even in the good tiled engine):

- **Adjacency constraints are ignored for tiled layouts.** `constraint_extractor.extract_constraints`
  produces MUST/SHOULD `AdjacencyConstraint`s, but `generate_layout` only forwards MUST pairs into
  `_place_rooms` via `must_adjacency_pairs`. `_tile_rooms` never receives them. In-row order is just
  input order.
- **Uniform row depth distorts proportions.** Every room in a zone row is given the same depth
  (`front_depth` / `private_depth`), so e.g. a kitchen ends up as deep as a living room. Proportional
  width-fill (`_fill_row`) can also turn one room into a wide thin strip beside a small one.

---

## Phase 1 — Unify all building types onto the space-filling tiler

**Goal:** eliminate blank space everywhere by routing every building type through `_tile_rooms`.

Changes in `layout_service.py`:

1. **Extend zone classification** so commercial room types tile cleanly:
   - `_TILED_FRONT_TYPES` (public-facing): add `workspace` is *not* front — keep it private/work.
     Add commercial public rooms: `reception`, `waiting_room`, `retail_display`, `checkout` are
     already present. Confirm `classroom` lands in a sensible row (treat as a "work/private" big room).
   - `_TILED_PRIVATE_TYPES` (work/quiet): already has `office`, `study`, `workspace`, `meeting_room`,
     `consultation_room`. Add `classroom`.
   - `_TILED_SERVICE_TYPES`: already has `bathroom`, `storage`, `utility`. Confirm fine for commercial.
   - Anything unclassified falls to the `other` row, which already fills width — so no blank gaps.
2. **Expand `_TILED_BUILDING_TYPES`** to include `office`, `clinic`, `retail`, `restaurant`, `school`,
   `classroom` (and the catch-all default). Effectively the tiler becomes the single engine.
3. **Keep `_place_rooms` / `_repair_rooms` as a fallback only** (e.g. if a future building type opts
   out). They are no longer on the default generation path. Do not delete — preserves test coverage
   and the `offsets = (0.0, 0.5, 1.0)` multi-candidate path for any non-tiled type.
4. The single-candidate path (`offsets = (0.0,)`) already applies to tiled types; with everything
   tiled, generation produces one deterministic candidate per prompt.

**Acceptance:** every `BENCHMARK_PROMPTS` entry (including office/clinic/retail/classroom) produces a
layout whose room area sums to ≥ ~80% of the footprint rectangle (no large blank band), with zero
overlaps and rooms inside the footprint.

---

## Phase 2 — Real adjacency reasoning (priority)

**Goal:** the parser's relational constraints actually shape placement in the tiled engine.

Changes:

1. **Thread constraints into `_tile_rooms`.** `_build_layout_candidate` already receives
   `must_adjacency_pairs`; extend it to also carry SHOULD pairs (new `should_adjacency_pairs`) and
   pass both into `_tile_rooms`.
2. **In-row ordering.** Inside each zone row (front / back / other), reorder rooms so constrained
   pairs are consecutive (wall-to-wall). Generalize the existing `_sort_by_adjacency` to weight MUST
   over SHOULD, and apply it per-row in the tiler (currently only used in `_place_rooms`).
3. **Cross-row X anchoring.** After rows are placed, if room A (row N) MUST be adjacent to room B
   (row N±1), shift A horizontally within its row so its X-span overlaps B's X-span (they share the
   horizontal wall between rows). Only nudge within the row; never break the zero-gap wall sharing or
   push a room outside the footprint.
4. **Interleave is constraint-aware.** `interleave_service` currently attaches a service room after
   every 2nd private room positionally. Prefer attaching a `bathroom`/`ensuite` to the bedroom it is
   constrained to (MUST `ensuite`, SHOULD `near`), falling back to the positional rule.

**Acceptance:**
- `kitchen`+`dining_room` (implicit SHOULD) share a wall in the front row.
- A `master_bedroom with ensuite` prompt places the bathroom wall-to-wall with that bedroom.
- `reception`+`waiting_room` (clinic/office) sit adjacent.
- Existing avoid-adjacency expectations (kitchen not next to bedroom) still hold.

---

## Phase 3 — Per-room depth & aspect-ratio clamping (priority)

**Goal:** realistic room proportions; no wide-thin strips, no over-deep service rooms.

Changes to `_fill_row` / `_tile_rooms`:

1. **Aspect clamp.** After proportional width assignment, clamp each room's width so width:depth
   stays within ~`[0.6, 2.6]`. If a room would be too wide for the row depth, cap its width and
   redistribute the freed width to its row-neighbors (still filling the row exactly).
2. **Two-tier depth within a row (optional sub-split).** Where a row mixes a large room (living) with
   small ones (bathroom/storage), allow the small rooms to occupy a shallower sub-cell and stack a
   second small room behind them in the same row depth, rather than stretching one small room to the
   full row depth. Implement as a localized 2-row split inside the zone band when a room's target area
   is < ~50% of `row_depth × assigned_width`. Keep it deterministic and overlap-free.
3. **Respect target area.** Width × depth for each room should land within the room's
   `typical_area_sqm_min/max` (from `_size_room_specs`) after tiling — verify the post-tile area does
   not blow past the max because of width-fill. Where proportional fill would exceed the max, cap and
   let an adjacent room absorb the slack.

**Acceptance:** `test_benchmark_room_sizes_stay_within_realistic_ranges` passes for all benchmark
prompts (extend it to assert post-tile areas, not just pre-tile sizing); no room has width:depth
outside the clamp range; zero overlaps; footprint still fully filled.

---

## Testing

- New file `backend/app/tests/test_sprint16_unified_layouts.py`:
  - Office / clinic / retail / classroom prompts tile with ≥80% footprint utilization (no blank band).
  - Adjacency: kitchen↔dining, master↔ensuite, reception↔waiting share walls.
  - Aspect-ratio clamp holds for all benchmark prompts.
  - Multi-floor commercial (e.g. 2-storey office) keeps shared building width + aligned stairs.
- Update `test_layout_service.py` / `test_layout_benchmarks.py` where they encode row-band semantics
  for commercial types (those layouts now tile).
- Full backend suite must stay green (currently 409 passing); frontend `npx tsc --noEmit` clean.

---

## Deferred beyond Sprint 16

- Phase 4: quality-scorer space-utilization + parser-tied adjacency-satisfaction metrics.
- Phase 5: 2D floor-plan view mode, door openings in partition walls, room-type color legend.
- True internal wall topology (shared-wall dedup, openings).
- Paid AI / model-based generation, CAD/BIM, structural validation.
