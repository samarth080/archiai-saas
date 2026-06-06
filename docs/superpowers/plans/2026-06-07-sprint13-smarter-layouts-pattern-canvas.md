# Sprint 13 — Smarter Layouts, Pattern Learning, and Better Canvas

> **Status:** In Progress
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
- [ ] Task 2: Pattern audit and validation
- [ ] Task 3: Pattern normalization
- [ ] Task 4: Pattern-weighted rule resolver
- [ ] Task 5: Adjacency-aware placement engine
- [ ] Task 6: Footprint and layout sanity checks
- [ ] Task 7: Wall, door, and window placeholders
- [ ] Task 8: Canvas visual polish
- [ ] Task 9: Quality feedback and insights
- [ ] Task 10: Benchmark suite
- [ ] Task 11: Pattern data workflow documentation
- [ ] Task 12: Final checks and sprint completion

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

Manual QA:

- Generate a 2-floor apartment, clinic, office, retail shop, classroom, and studio.
- Confirm pattern source and quality insights are visible.
- Inspect 3D, top, and floor-plan style views.
- Move/edit/save/export/share a layout.
- Confirm normal users do not see scraper/data-pipeline tooling as a primary workflow.

