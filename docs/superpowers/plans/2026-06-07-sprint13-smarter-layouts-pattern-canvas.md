# Sprint 13 — Smarter Layouts, Pattern Learning, and Better Canvas

> **Status:** Complete
> **Branch:** `sprint-13/smarter-layouts-pattern-canvas`
> **Started:** 2026-06-07

## Goal

Improve ArchiAI layout quality without paid AI APIs by using structured public layout-pattern data as deterministic generation knowledge.

The learning loop for this sprint is:

```text
public text
-> scraper
-> LayoutPattern rows
-> normalization and validation
-> pattern rules
-> layout generation
-> quality scoring
-> clearer canvas rendering
```

This keeps the MVP affordable and explainable for students. The scraper remains internal tooling; normal users should experience the result as cleaner generated layouts and a better canvas, not as a data-pipeline feature.

## Scope

- Improve pattern validation, normalization, confidence handling, and rule resolution.
- Improve deterministic room placement using zones, adjacency, and simple footprints.
- Add lightweight architectural markers for concept clarity.
- Polish the canvas visual presentation without changing it into CAD/BIM.
- Expand quality insights and benchmark coverage.

## Out Of Scope

- Paid AI APIs, OpenAI, Claude, Gemini, or local model training.
- CAD/BIM export or structural validation.
- Realistic construction-grade doors, windows, or stairs.
- Advanced optimization algorithms.
- Public scraper/source-management workflow for normal users.

## Task Checklist

- [x] Task 1: Sprint 13 plan and tracker
- [x] Task 2: Pattern audit and validation
- [x] Task 3: Pattern normalization
- [x] Task 4: Pattern-weighted rule resolver
- [x] Task 5: Adjacency-aware placement engine
- [x] Task 6: Footprint and layout sanity checks
- [x] Task 7: Wall, door, and window placeholders
- [x] Task 8: Canvas visual polish
- [x] Task 9: Quality feedback and insights
- [x] Task 10: Benchmark suite
- [x] Task 11: Pattern data workflow documentation
- [x] Task 12: Final checks and sprint completion

## Implementation Notes

- Pattern validation now prevents malformed or low-confidence scraped records from influencing generation.
- Pattern normalization gives prompt parsing, scraper extraction, and pattern lookup a shared vocabulary.
- Pattern resolution tracks applied and ignored pattern counts in layout metadata.
- Placement uses zone rows, adjacency-aware row spacing, and forward-only anchoring to prevent duplicate-room overlap.
- Layout JSON now includes simple floor footprints and lightweight wall, door, and window marker objects.
- Canvas view modes now include 3D, top view, and floor-plan view.
- Quality insights include suggestions and pattern-source metadata.
- Benchmark coverage now asserts no overlaps, minimum quality score, and key non-residential adjacencies.

Pattern data workflow reference: `docs/PATTERN_DATA_WORKFLOW.md`.

## Verification Plan

Backend:

```powershell
cd backend
pytest
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
npm test -- --run
```

Final verification completed:

- `cd backend; pytest` — 252 passed, 1 warning
- `cd frontend; npx tsc --noEmit` — passed
- `cd frontend; npm run build` — passed
- `cd frontend; npm test -- --run` — 19 files passed, 89 tests passed

Manual QA:

- Generate a 2-floor apartment, clinic, office, retail shop, classroom, and studio.
- Confirm pattern source and quality insights are visible.
- Inspect 3D, top, and floor-plan style views.
- Move/edit/save/export/share a layout.
- Confirm normal users do not see scraper/data-pipeline tooling as a primary workflow.
