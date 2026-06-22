# ArchiAI — CLAUDE.md

This file is the source of truth for any AI agent (Claude, Codex, Gemini, or other) working on this codebase. Read it fully before making any changes.

---

## What This Project Is

ArchiAI is an AI-powered architectural design platform. Users enter a natural language design brief and receive a 3D architectural layout they can view, edit, and refine in an interactive browser-based canvas.

Full product strategy: [`docs/PROJECT_STRATEGY.md`](docs/PROJECT_STRATEGY.md)
Sprint 1 design spec: [`docs/superpowers/specs/2026-05-23-sprint1-auth-design.md`](docs/superpowers/specs/2026-05-23-sprint1-auth-design.md)

---

## Multi-Agent Environment

**This code is written by Claude and reviewed by other agents including Codex.**

Rules for all agents:
- Read this file and the relevant spec before touching any code
- Do not change the project structure without updating this file
- Do not introduce dependencies not listed in the tech stack below without flagging it
- Do not modify another agent's completed and committed work without a clear reason documented in the commit message
- If you are unsure about scope, read the sprint spec before proceeding
- Leave code cleaner than you found it — fix obvious issues in files you touch, but do not refactor unrelated code

If you are Codex or another reviewing agent:
- Check code against the spec in `docs/superpowers/specs/`
- Flag any deviation from the agreed design
- Do not auto-fix — report findings so the lead agent (Claude) can action them

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Zustand, Axios, React Hook Form |
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (HS256, python-jose), bcrypt (passlib) |
| 3D Canvas | Three.js, React Three Fiber, @react-three/drei (Sprint 4+) |
| Dev | Docker, Docker Compose |
| Testing | Pytest, httpx (backend) |

---

## Project Structure

```
archiai-saas/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config/settings.py
│   │   ├── database/connection.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/
│   │   ├── services/
│   │   ├── utils/
│   │   └── tests/
│   ├── alembic/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── store/
│   │   ├── services/
│   │   ├── hooks/
│   │   └── utils/
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── PROJECT_STRATEGY.md
│   └── superpowers/specs/
├── docker-compose.yml
├── .env.example
├── CLAUDE.md               ← this file
└── README.md
```

---

## Sprint Progress

Sprints 0–16 are complete. Full task-by-task detail for each is archived in [`docs/SPRINT_HISTORY.md`](docs/SPRINT_HISTORY.md) — below is a one-line summary of each so this file stays readable. The active sprint (17+) is kept in full below the summary.

| Sprint | Headline |
|---|---|
| 0 | Product strategy, Sprint 1 spec, repo created |
| 1 | Auth (register/login/logout/me, JWT) + React/Tailwind scaffold + protected routes |
| 2 | Global error handler shape; Project CRUD + ActivityLog |
| 3 | Shared Axios instance; dashboard rebuild; project workspace page |
| 4 | First R3F 3D canvas — OrbitControls, room selection, TransformControls |
| 5 | First layout generation — `prompt_service`/`layout_service`, multi-floor support |
| 6 | Direct drag-to-move editing, duplicate/delete, editor toolbar, save/version persistence |
| 7 | Version list, project duplicate, thumbnails, empty/loading/error states |
| 8 | Prompt refinement (add/remove/resize ops) with a Generate/Refine toggle |
| 9A | Version history drawer + restore-to-canvas |
| 9B | Project-scoped activity log endpoint + drawer |
| 9C | Auto-save drafts (`auto_draft` versions) + recovery banner |
| 9D | Team workspaces — roles, member management, shared projects |
| 10 | Robots.txt-respecting scraper + `LayoutPattern` extraction + monitoring UI |
| 11 | Pattern-weighted sizing/zoning/adjacency, quality scoring, generation insights UI |
| 12 | PNG/PDF export, shareable read-only links, MVP UI polish, deployment readiness |
| 13 | Pattern validation/normalization, adjacency-aware placement, canvas visual polish |
| 14 | 10-stage deterministic NLU parser (normaliser → building inference → constraints → sizing); Vastu module |
| 15 (+ Phase 2) | Multi-pass overlap repair, partition walls, the zero-gap tiler for residential types |
| 16 | Tiler unified across all building types incl. commercial; MUST/SHOULD adjacency threading; template/synonym gap fixes |

---

### Sprint 17+ — 10× Roadmap 🚧 In Progress (Phases 0, 1 & 2 underway)

> Full roadmap: [`docs/superpowers/plans/2026-06-22-10x-roadmap.md`](docs/superpowers/plans/2026-06-22-10x-roadmap.md)
> Branches: `sprint-17/dimensions-on-canvas` (Phase 1, off `main`), `sprint-17/phase0-design-params` (Phase 0 + the Phase 2 doors/dimensions fixes, stacked on top of it). Neither is pushed yet — this machine's GitHub credentials (`udai-shunya`) lack write access to `samarth080/archiai-saas`; push once that's resolved.

A longer-horizon plan to move from "concept layout MVP" to a standout product, reverse-engineered from Hypar's parametric-generative approach. Five pillars, sequenced into phases:

- **Pillar A — Real planning engine:** replace row/tile packing with a BSP/slicing-tree space partitioner for a true building envelope, plus a real circulation graph, doors on the path, and orientation-aware windows.
- **Pillar B — Dimensions & interaction:** on-canvas dimension lines + area badges on click/select (not just the Inspector side panel), a metrics HUD, CAD-lite snapping.
- **Pillar C — Data learning:** swap the scraper's fetcher to Scrapling (handles JS/anti-bot sites like ArchDaily/Dezeen), extract structured project data (not just visible text), aggregate into statistical priors (area distributions, adjacency probabilities) feeding the existing `LayoutPatternRules` pipe.
- **Pillar D — UI/UX overhaul:** single-screen layout (brief/params, canvas + option gallery, inspector/metrics), muted architectural palette, option gallery for generated candidates, command palette, dimensioned plan-view rendering with door swings.
- **Pillar E — Interop & hardening:** SVG/DXF/glTF export, production frontend build (currently Docker serves the Vite dev server), refresh-token auth hardening.

Phased rollout: Phase 0 (pipeline refactor + `DesignParams`) → Phase 1 (dimensions + UI shell) → Phase 2 (BSP planning engine + circulation) → Phase 3 (Scrapling + priors) → Phase 4 (optioneering + export) → Phase 5 (optional ML + IFC, later).

**Phase 0 progress (DesignParams + first parametric levers):**
- [x] `DesignParams` schema (`plotWidthM`, `plotDepthM`, `floors`, `orientation`, `vastu`) added to `GenerateRequest` as a fully optional sibling of `prompt` — omitting it leaves generation byte-for-byte unaffected
- [x] `plot_width_m` wired end-to-end: overrides the tiled building's program-area-inferred footprint width, clamped to 4-40m (wider than the 7-22m inferred default since a real plot can legitimately fall outside that heuristic's range); holds consistently across multi-floor layouts
- [x] `floors` and `vastu` DesignParams route through the existing `total_floors`/`vastu_requested` parameters, taking precedence over the prompt when supplied
- [x] `orientation` (S/N/E/W, default S) wired end-to-end: picks which exterior wall is the entry/road-facing side via `_ORIENTATION_ENTRY_WALL`; windows are placed on the other three exterior walls (previously always exactly one window on one fixed wall, regardless of building shape)
- [x] `plot_depth_m` still only accepted/recorded in `metadata.designParams`, not yet applied to geometry — needs the BSP partitioner (Phase 2) to constrain depth without distorting room proportions the way a naive clamp would
- [x] Fixed a pre-existing gap found along the way: `FloorResponse` was silently dropping `footprint` from every API response (the schema never declared the field), which meant the Phase 1 metrics HUD's footprint-utilization stat could never populate for API-loaded layouts; `footprint` is now part of the response schema
- [x] Collapsible "Plot params" row in the Project prompt bar — plot width, floors, and an "Entry faces" direction select (all blank/"auto" by default) — sends `designParams` alongside the prompt when filled in
- [x] Backend + frontend tests cover plot width override/clamping/multi-floor consistency, orientation's effect on entry/window placement, API plumbing, and no-params regression
- [ ] The full `Fn`-pipeline decomposition of `generate_layout` into composable functions over a shared `BuildingModel` (the architectural part of Phase 0) is deferred — the `DesignParams` plumbing was delivered as a safe, additive slice instead of risking the 440+ test layout engine on a large simultaneous rewrite; revisit when Phase 2's BSP partitioner needs the pipeline shape anyway
- [ ] `plot_width_m`/`orientation` only affect tiled building types (`_TILED_BUILDING_TYPES`) — row-banded fallback types ignore them (in practice this covers nearly everything generated since Sprint 16)

**Phase 1 progress (dimensions + UI shell):**
- [x] `showDimensions` toggle added to `canvasStore` (default off)
- [x] `DimensionAnnotations.tsx` — width/depth dimension lines with end ticks, labelled in metres, rendered just outside a room's footprint; selected room renders them bold plus a centered area badge (`W × D m · area m²`); other rooms get the same lines in a faint style when the global toggle is on
- [x] Wired into `RoomMesh.tsx`, updates live during drag
- [x] `MetricsHud.tsx` — live room count, total area, and footprint-utilization % for the active floor, mirrored opposite `EditorToolbar`
- [x] "Dimensions" checkbox added to `EditorToolbar` next to the existing Snap toggle
- [x] Frontend tests for the new toggle (store + toolbar); full frontend suite green, `npx tsc --noEmit` clean
- [x] **Bug fix:** the global toggle rendered dimension lines for every room in *any* view mode, including the default 3D perspective camera — each line's fixed 0.45m offset landed inside neighbouring rows in a tightly tiled plan, so multiple rooms' labels piled on top of each other. Now restricted to plan/top view, where the convention actually reads cleanly; the selected room's own dimensions still show in any view mode.
- [ ] Hover-triggered dimensions on non-selected rooms (deferred — click/select only for now)
- [ ] Rotation-aware dimension lines (current lines assume axis-aligned rooms)
- [ ] `sq ft` unit toggle on the area badge

**Phase 2 progress (incremental slices, ahead of the full BSP rewrite):**
- [x] Every partition wall between two adjacent rooms whose shared span is >= 1.2m gets a door marker centred on it (`_generate_partition_walls`), so generated floor plans are walkable room-to-room instead of solid-walled boxes with only one entry door total
- [x] **Bug fix — wrong adjacency branch:** when one room's footprint was narrower than and fully nested inside another's span on one axis (e.g. an Office nested inside a wider Hallway), both gap measurements read near-zero and the code picked the wrong wall orientation, so Hallway↔room walls/doors were silently never generated at all. Fixed by comparing real overlap magnitude on each axis instead of relying on which gap happened to read near zero.
- [x] **Bug fix — doors routed wrong:** even with the geometry fixed, every adjacent pair got a direct door unconditionally, so two private/service cells sitting side by side (e.g. Office next to Bathroom) each got a lateral door to each other instead of each opening onto the corridor. `_wants_direct_door` now gates this: the corridor always connects to whatever it touches, open-plan public rooms still connect directly to each other, but two private/service cells only get a direct door when there's no corridor on the floor to route through instead.
- [x] Tests cover door placement, span-matching, the 1.2m minimum-span cutoff, the corridor-routing fix specifically (regression test against the exact clinic layout that surfaced the bug), and that open-plan public rooms still connect directly
- [x] `layout_service.py` given a module docstring + section banners (comments only, zero logic change) documenting the two-engine history, since that's exactly the kind of file where a bug like the corridor-nesting one hides
- [ ] The full BSP/slicing-tree space partitioner, real circulation graph, and door-clearance checks (the rest of Phase 2) are not started — these slices only add doorways to walls the existing tiler already draws, they don't change how rooms are placed

Not yet started: the rest of Phase 2 (BSP planning engine + circulation graph), Phase 3 (Scrapling), Phase 4 (optioneering/export), Phase 5 (optional ML/IFC). Pillar D's palette/UI-polish work was deliberately skipped this round — it's subjective and couples to a hardcoded test color assertion, lower priority than shipping working features.

---

## Development Rules

- **Never hardcode secrets.** All credentials and keys go in `.env` (gitignored). Use `.env.example` for documentation.
- **Never push directly to `main`.** Use feature branches. Branch naming: `sprint-1/feature-name`.
- **Write tests before or alongside code**, not after.
- **Every significant action must be logged.** Canvas edits, generation events, team changes — all go to `ActivityLog`.
- **Keep modules separate.** Frontend, backend, AI logic, scraper, and logging are distinct. Do not mix concerns.
- **No TODOs in committed code.** If something is deferred, document it in the sprint spec or a GitHub issue.
- **Mouse drag-and-drop in the 3D canvas must work directly.** Inspector editing is a complement, not the primary UX.
- **Auto-save must never overwrite named version history.** Drafts are separate from named versions.

---

## Environment Setup

```bash
git clone https://github.com/samarth080/archiai-saas.git
cd archiai-saas
cp .env.example .env
docker-compose up
```

- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

---

## Key Docs

| Document | Purpose |
|---|---|
| `docs/PROJECT_STRATEGY.md` | Full product strategy, all 20 sections |
| `docs/SPRINT_HISTORY.md` | Full task-by-task detail for completed Sprints 0–16 |
| `docs/superpowers/specs/2026-05-23-sprint1-auth-design.md` | Sprint 1 detailed design spec |

---

## Contact / Ownership

Project: ArchiAI
Repo: `github.com/samarth080/archiai-saas`
Lead: samarth080
