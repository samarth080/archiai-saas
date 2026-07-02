# Hypar-Inspired Product Strategy

Hypar's parametric-generative workflow is **inspiration, not imitation**. We take
the *ideas* — a live program, scored alternatives, a metrics-rich single screen,
the designer always in control — and express them in ArchiAI's own deterministic,
non-ML engine and our own UI. We do not copy Hypar's branding or UI.

## Principles

- **Designer in control.** Automation assists; it never overrides. The generator
  proposes; the user edits, picks, and saves. Nothing auto-saves over named
  history.
- **Everything explainable.** Because generation is rule/graph-based (see
  `NON_ML_GRAPH_LAYOUT_ENGINE.md`), every candidate can show *why* it scored the
  way it did — quality reasons, warnings, applied rules.
- **One screen.** Brief/params, canvas + option gallery, and inspector/metrics
  coexist without route hops.

## Building blocks (status)

- **Program tracking** — target vs. actual area per space, live. The
  `ProgramGraph` (Phase 2) already carries per-node `target_area_sqm`; surfacing
  a target-vs-actual panel is the next UI step.
- **Option gallery** — the generator already builds multiple scored candidates
  (tiler vs. BSP; parameter variants) and returns the losers as pickable
  `alternatives`; the gallery renders them and swaps one into the canvas on click
  (Sprint 17 Phase 4). Growing to a 6–12 candidate parameter sweep is future work.
- **Metrics dashboard** — live room count, total/usable area, footprint
  utilization (Phase 1 `MetricsHud`); to be extended with circulation ratio,
  daylight proxy, and adjacency-satisfaction score once the graph-driven scorer
  lands.
- **Direct manipulation** — drag with footprint clamping, 8-point resize handles,
  click-to-place, tape measure, undo/redo (Phase 1) so the designer can always
  override any generated result.
- **Program import** (future) — CSV/XLSX room list → `ProgramGraph` via the
  existing adapters, round-tripping to a layout.
- **Command palette** (future, ⌘K) — fast access to tools/actions.

## What this is NOT

- Not an ML/generative-black-box product — the value is a transparent,
  editable, deterministic engine.
- Not a Hypar clone — no shared UI, branding, or function library.
