# Sprint 11 - Layout Improvement Using Pattern Data

> **Date:** 2026-05-31  
> **Status:** In Progress  
> **Branch:** `sprint-11/layout-improvement`

## 1. Sprint Goal

Improve ArchiAI's deterministic layout generator so concept layouts feel more realistic and architecture-aware without requiring paid AI services or external model APIs.

Sprint 11 builds on the existing rule-based engine rather than replacing it. The generator must continue to work when the database contains no scraped pattern records.

## 2. Why Sprint 10 Pattern Data Matters

Sprint 10 introduced a responsible public-text reference pipeline and structured `LayoutPattern` records. Those records can provide source-derived hints for:

- Room size ranges
- Room zones
- Preferred adjacencies
- Avoid-adjacency rules
- Room-to-total-area ratios
- Layout-pattern names
- Circulation and opening notes
- Confidence levels

Pattern data improves defaults when present. It is advisory input, not a hard dependency and not training data for an AI model in this sprint.

## 3. MVP Scope

- Add benchmark tests for representative prompt categories.
- Read structured pattern data through an isolated service.
- Use realistic fallback size ranges when no pattern data exists.
- Apply optional pattern-derived size ranges and room-to-area ratios.
- Improve public, private, service, and circulation zoning.
- Improve deterministic adjacency ordering and obvious bad-placement avoidance.
- Add small building-type templates for apartments, studios, houses, offices, clinics, classrooms, and retail/store layouts.
- Improve rule-based prompt extraction for common architectural phrases and total-area values.
- Add a deterministic layout-quality scoring utility.
- Expose generation insights in a minimal read-only editor panel.
- Document future AI integration options without runtime integration.

## 4. Excluded Scope

- Paid AI APIs or external LLM calls
- OpenAI, Claude, Gemini, or other provider SDK dependencies
- API keys, billing, credits, or rate-limit infrastructure
- Full AI model training, fine-tuning, embeddings, or vector search
- Local model runtime integration
- Learning automatically from user edits
- Complex spatial optimization or structural engineering validation
- Production-grade CAD/BIM reasoning
- Replacing the existing layout engine wholesale

## 5. Current Generation Limitations

The current layout engine:

- Uses one fixed size per room type with simple prompt modifiers.
- Supports a small room vocabulary focused on residential layouts.
- Places room blocks in broad public/private/other rows.
- Does not read Sprint 10 `LayoutPattern` records.
- Does not represent zones explicitly on generated rooms.
- Uses no building-specific generation templates.
- Has no quality score or readable applied-rule diagnostics.
- Does not parse total-area requirements.

These limitations are acceptable foundations. Sprint 11 extends them in small, testable steps.

## 6. Layout Pattern Usage Plan

Add an isolated pattern-access service that can:

1. Query room size ranges by `building_type` and `room_type`.
2. Query adjacency and avoid-adjacency relationships.
3. Query preferred room zones.
4. Query known layout patterns by building type.
5. Filter low-confidence records where a stronger source-derived record exists.
6. Return deterministic fallback defaults when the database has no matching data.

The layout generator should receive resolved rule data rather than issue database queries directly. API generation can resolve optional database-backed rules before calling the pure layout function.

## 7. Rule Improvement Plan

Deterministic rules should improve:

- Room dimensions using realistic size ranges and prompt area allocation.
- Public/private/service/circulation grouping.
- Living room, kitchen, and dining proximity.
- Entry-to-public-zone proximity.
- Bedroom grouping and quieter placement.
- Bathroom proximity to bedroom or corridor groups.
- Reception proximity to entry for office and clinic templates.
- Meeting-room proximity to work areas.
- Classroom connection to circulation.
- Consistent stair placement on multi-floor layouts.

Rules remain concept-level. They do not claim code-compliant architectural validation.

## 8. Building Template Plan

Add compact deterministic templates:

| Template | Intended Behavior |
|---|---|
| `apartment` | Public living cluster, grouped private bedrooms, service support |
| `studio` | Compact open-plan living/sleeping emphasis |
| `house` | Residential grouping with public-ground/private-upper preference |
| `office` | Entry/reception, work area, meeting and support spaces |
| `clinic` | Entry/waiting/reception separated from consultation and support |
| `classroom` | Classroom spaces connected through circulation/common zones |
| `retail` | Entry/checkout/display public area with rear storage/support |

Templates define default room groups, sizing defaults, zone priorities, adjacency priorities, pattern strategy, multi-floor preferences, and fallback behavior.

## 9. Prompt Extraction Improvement Plan

Extend rule-based extraction for:

- `open plan kitchen living`
- `ensuite master bedroom`
- `home office`
- `small clinic with waiting and consultation rooms`
- `office with reception, meeting room and open workspace`
- `studio apartment with balcony`
- `2 floor house with bedrooms upstairs`
- `retail shop with storage and checkout`
- `120 sqm`
- `120 square meters`
- `1000 sq ft`

Keep extraction deterministic. Do not add an LLM dependency.

## 10. Benchmark Prompt Plan

Create benchmark fixtures for:

- One-bedroom studio apartment
- Two-bedroom apartment
- Three-bedroom apartment
- Small house
- Two-floor house
- Small office
- Clinic layout
- Classroom layout
- Retail/store layout

Benchmarks should validate required rooms, realistic sizes, zones, important adjacency goals, avoid-adjacency behavior where practical, multi-floor compatibility, backward-compatible JSON, and fallback behavior without stored patterns.

## 11. Layout Quality Scoring Plan

Add a diagnostic utility returning:

```json
{
  "score": 86,
  "reasons": ["Required rooms are present"],
  "warnings": ["Bathroom is not near a corridor or bedroom"],
  "appliedRules": ["template:apartment", "zone:public-private-split"]
}
```

Score inputs:

- Required-room presence
- Realistic room sizes
- Preferred adjacency satisfaction
- Avoid-adjacency violations
- Zone grouping quality
- Multi-floor stair/circulation presence
- Layout-schema validity
- Building-template fit

Scoring is diagnostic only. It should not block generation.

## 12. Minimal Insight UI

Add a small read-only insight section near the existing editor workflow showing:

- Detected building type
- Applied template
- Detected zones
- Quality score
- Warnings
- Applied deterministic rules

This is not an analytics dashboard and must not disrupt editing.

## 13. Future AI Placeholder

Future AI work may optionally add:

- LLM-based prompt understanding
- Model-based layout ranking
- Fine-tuned layout generation
- OpenAI, Claude, or Gemini providers configured only through environment variables
- Local model support through Ollama or Hugging Face
- Learning signals from user edits
- Cost, rate-limit, privacy, and data-safety controls

Sprint 11 does not implement any provider calls, keys, dependencies, or runtime integration.

## 14. Test Plan

Backend:

- Existing auth, project, design, workspace, draft, scraper, prompt, refinement, and layout tests remain green.
- Benchmark prompts generate backward-compatible layouts.
- Pattern access falls back cleanly when the database is empty.
- Stored high-confidence patterns improve resolved rule data.
- Sizing, template, adjacency, extraction, and scoring behavior receive focused tests.

Frontend:

- TypeScript passes.
- Existing tests remain green.
- Generation-insight UI renders without breaking the editor.
- Production build passes.

## 15. Task Checklist

1. Add Sprint 11 plan/spec.
2. Add benchmark prompt and quality tests.
3. Add layout-pattern access service.
4. Improve room-sizing rules.
5. Improve zoning and adjacency rules.
6. Add building-type layout templates.
7. Improve prompt requirement extraction.
8. Add layout-quality scoring.
9. Add minimal generation-insight UI.
10. Add future-AI placeholder documentation.
11. Run final checks and mark Sprint 11 complete.

## 16. Risks And Assumptions

- Pattern data may be sparse or absent, so fallbacks are mandatory.
- Scraped reference data is advisory and must not reproduce copyrighted layouts.
- Deterministic packing remains concept-level and may not optimize every footprint.
- Existing saved layouts must remain loadable; new JSON fields must be additive.
- Multi-floor behavior from Sprint 5 must stay intact.
- Pattern lookup should be isolated from the pure layout engine so tests remain fast and deterministic.
- The UI insight panel should remain read-only and compact.

## 17. Commit Plan

Create local commits only on `sprint-11/layout-improvement`. Do not push during the task sequence.

1. `Add Sprint 11 layout improvement plan`
2. `Add layout benchmark quality tests`
3. `Add layout pattern access service`
4. `Improve room sizing rules`
5. `Improve layout zoning and adjacency rules`
6. `Add building type layout templates`
7. `Improve prompt requirement extraction`
8. `Add layout quality scoring`
9. `Add layout generation insight UI`
10. `Add future AI integration placeholder documentation`
11. `Complete Sprint 11 layout improvement`
