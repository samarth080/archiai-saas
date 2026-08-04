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

### Sprint 0 — Product Planning ✅ Complete
- [x] Full product strategy written (`docs/PROJECT_STRATEGY.md`)
- [x] Sprint 1 design spec written and approved (`docs/superpowers/specs/2026-05-23-sprint1-auth-design.md`)
- [x] GitHub repo created: `github.com/samarth080/archiai-saas`
- [x] CLAUDE.md created

### Sprint 1 — Authentication and Project Setup ✅ Complete
- [x] Backend project scaffolded (FastAPI + SQLAlchemy + Alembic)
- [x] PostgreSQL via Docker Compose running
- [x] User model and migration
- [x] `POST /api/auth/register`
- [x] `POST /api/auth/login`
- [x] `POST /api/auth/logout`
- [x] `GET /api/auth/me`
- [x] JWT middleware
- [x] Auth tests passing (8 tests)
- [x] Frontend project scaffolded (React + TypeScript + Tailwind + Vite)
- [x] Landing page
- [x] Register page
- [x] Login page
- [x] Register/login forms display backend and network errors instead of generic failures
- [x] Dashboard page (protected, stub)
- [x] Zustand auth store
- [x] ProtectedRoute + PublicOnlyRoute wrappers
- [x] `docker-compose up` runs full stack

### Sprint 2 — Backend Foundation ✅ Complete
- [x] Global error handler returns `{ error, code, status }` for all HTTPExceptions
- [x] RequestValidationError also returns readable `{ error, code, status }` shape (422)
- [x] All existing auth tests updated and passing with new error format
- [x] `POST /api/projects` creates a project and logs `"project.created"` to ActivityLog
- [x] `GET /api/projects` returns only the authenticated user's projects
- [x] `GET /api/projects/{id}` returns 403 for another user's project
- [x] `PUT /api/projects/{id}` updates and logs `"project.updated"`
- [x] `DELETE /api/projects/{id}` deletes and logs `"project.deleted"`, returns 204
- [x] All 8 project tests passing
- [x] All 8 auth tests still passing
- [x] Alembic migrations 002 (projects) and 003 (activity_logs) added

### Sprint 3 — Frontend Foundation ✅ Complete
- [x] Shared Axios instance (`src/services/api.ts`) injects Bearer token on every request
- [x] Shared Axios instance defaults to `http://localhost:8000` when `VITE_API_URL` is not provided in local frontend env
- [x] Auth service uses the shared Axios instance so register/login follow the same API URL and token behavior
- [x] 401 responses log the user out and redirect to `/login`
- [x] Dashboard rebuilt: sidebar + responsive card grid + real data from `GET /api/projects`
- [x] Dashboard guards invalid project-list responses so API/config mistakes show an error instead of crashing React
- [x] "+ New Project" modal — calls `POST /api/projects`, prepends project to grid on success
- [x] ProjectCard click navigates to `/projects/:id`
- [x] Project workspace page (`src/pages/Project/index.tsx`) — loads from `GET /api/projects/:id`
- [x] Edit mode updates title/description via `PUT /api/projects/:id`
- [x] Delete button confirms, calls `DELETE /api/projects/:id`, redirects to dashboard
- [x] Empty state, loading state, and inline error states throughout
- [x] `/projects/:id` added as a protected route in `App.tsx`
- [x] TypeScript compilation clean (`npx tsc --noEmit`)
- [x] Canvas placeholder in place for Sprint 4

### Sprint 4 — Basic 3D Canvas ✅ Complete

- [x] Shared `<Sidebar>` component extracted; Dashboard and Project pages use it
- [x] `three`, `@react-three/fiber@8`, `@react-three/drei@9`, `@types/three` installed
- [x] R3F canvas renders in the Project workspace with correct lighting and grid
- [x] Camera orbits, zooms, and pans with mouse (OrbitControls)
- [x] 5 hardcoded room boxes visible, each a different color
- [x] Clicking a room selects it (emissive highlight) and opens the Inspector panel
- [x] Clicking empty canvas deselects (Inspector closes)
- [x] TransformControls gizmo appears on selected room; dragging it moves the room
- [x] OrbitControls disabled while TransformControls is active (no camera fighting)
- [x] Inspector X/Z fields and size fields update/move the room in real time
- [x] Delete button in inspector removes the room from the scene
- [x] Canvas state is in-memory only (persistence in Sprint 7)
- [x] `npx tsc --noEmit` passes with zero errors
- [x] 8 canvas store tests passing

### Sprint 5 — Basic 3D Layout Generation ✅ Complete

- [x] `prompt_service.py` extracts room types, counts, and size modifiers from natural language
- [x] `layout_service.py` places rooms in two zones (public/private) with 1m gaps, 2m between zones
- [x] `POST /api/design/generate` returns layout JSON; protected by JWT (DB-backed auth)
- [x] Bottom prompt bar in Project workspace — textarea + Generate button
- [x] Generated rooms replace hardcoded canvas rooms via `canvasStore.loadRooms`
- [x] Loading state (button disabled + "Generating…") during API call
- [x] Error message shown if generation fails or no rooms detected; API error propagated to user
- [x] Floor count extraction supports numeric, word-based, storey/story, G+N, and ground-plus prompts
- [x] Layout JSON includes `metadata.totalFloors`, `building.floorHeight`, and `floors[]`
- [x] Multi-floor layouts assign each generated object to exactly one floor
- [x] Multi-floor layouts add simple aligned `Stairs` placeholders on every floor
- [x] Top-level `rooms` remains available for backward compatibility
- [x] Design and first DesignVersion models/migration added for generated layouts
- [x] Project-scoped generation saves layout JSON to Design and DesignVersion when `projectId` is supplied
- [x] Project workspace generation sends `projectId` so generated layouts are saved for the project
- [x] `POST /api/design/generate` logs `"design.generated"` through ActivityLog
- [x] Prompt service, layout service, and design API tests cover generation behavior
- [x] Backend tests passing (56 tests)
- [x] `npx tsc --noEmit` passes with zero errors

### Sprint 6 — 3D Editing Workflow ✅ Complete

- [x] Canvas state supports object type, rotation, grid snap, save status, floor assignment, and edit activity entries
- [x] Inspector supports label editing, object type editing, floor assignment, precise X/Z movement, precise resize, precise rotation, duplicate, and delete
- [x] Canvas renders object labels above rooms/components
- [x] Clicking a room/component selects only that object and shows a visible highlight
- [x] Direct mouse drag moves the selected object on the X/Z plane while preserving floor/elevation
- [x] Orbit controls are disabled while direct object drag is active
- [x] Direct drag respects snap-to-grid when enabled
- [x] Sprint 6 bug fix: removed unstable selected-object `TransformControls` wrapper so selection and pointer drag stay on the same mesh
- [x] Sprint 6 bug fix: empty-canvas deselect no longer competes with object click/drag events
- [x] Ctrl+D / Cmd+D duplicates the selected object
- [x] Delete / Backspace removes the selected object
- [x] Editor toolbar supports snap toggle, floor selector, add-object panel, duplicate, delete, and save status
- [x] Add-object panel can create room, wall, door, window, stair, floor, and open space objects on the selected floor
- [x] Duplicate preserves type, dimensions, rotation, and floor assignment with a small X/Z offset
- [x] Single-floor layouts continue to render and edit through the backward-compatible top-level `rooms` structure
- [x] Multi-floor layouts render through `floors[]`; selected floor mode edits one floor, All Floors shows stacked elevations
- [x] Project workspace loads the latest saved Design layout for the project when available
- [x] Save Layout persists edited layout JSON to Design and creates a new DesignVersion
- [x] `PUT /api/design/{design_id}` logs `"layout.saved"` through ActivityLog
- [x] In-memory activity log records add, move, resize, rotate, rename, duplicate, and delete edits
- [x] Debounced in-memory auto-save status shows Saving then Saved after edits
- [x] Canvas store tests expanded to 20 passing tests
- [x] Backend design save/load tests passing as part of 58 backend tests
- [x] Frontend production build passes
- [x] Sprint 6 implementation note exists at `docs/superpowers/plans/2026-05-27-sprint6-3d-editing-workflow.md`
- [ ] Persistent per-object ActivityLog API remains deferred to Sprint 9

### Sprint 7 — Database and Project Management ✅ Complete

- [x] Project CRUD, rename, and delete remain project-owner scoped
- [x] Project delete removes related Design and DesignVersion rows so persisted layouts do not block deletion
- [x] Manual Save Layout creates a named/manual DesignVersion with incrementing version number, snapshot JSON, change summary, creator, and timestamp
- [x] Generated layouts continue to create the first generated DesignVersion
- [x] `GET /api/projects/{id}/versions` lists project versions newest first with useful metadata
- [x] `POST /api/projects/{id}/duplicate` creates a separate project copy with latest design/layout snapshot
- [x] Project duplicate creates its own initial DesignVersion and does not copy old activity logs
- [x] Project thumbnails are captured from the canvas on Save Layout and persisted on Project
- [x] Dashboard ProjectCard displays saved thumbnails or a clean placeholder
- [x] Opening a project loads the latest saved design/layout when available
- [x] Empty projects show a clear empty editor state instead of hardcoded starter rooms
- [x] Save status distinguishes Unsaved changes, Saving, Saved with timestamp, and Error
- [x] Alembic migration 005 adds Sprint 7 project thumbnail and version metadata fields
- [x] Backend Sprint 7 tests cover versions, duplicate, thumbnail persistence, latest load, and delete-with-designs behavior
- [x] Frontend canvas store tests cover empty layout clearing and unsaved state
- [ ] Full version history panel deferred to Sprint 9
- [ ] Restore version UI deferred to Sprint 9
- [ ] Collaboration/version-control UI deferred to Sprint 9

### Sprint 8 — Prompt Refinement ✅ Complete

- [x] `refinement_service.parse_refinement` extracts AddOp / RemoveOp / ResizeOp from natural language
- [x] `refinement_service.apply_refinement` mutates the layout append-only (existing room positions preserved)
- [x] RESIZE → REMOVE → ADD application order; multi-floor ADD routes by Sprint 6 zone+floor rules
- [x] `POST /api/design/refine` returns the updated layout plus a `refinementSummary` string
- [x] Successful refine inserts `DesignVersion(version_type='refined', change_summary=summary)` and logs `design.refined`
- [x] 422 with help text when the prompt produces no ops; 422 with "No matching rooms" when ops are all no-ops
- [x] Generate / Refine segmented toggle on the bottom prompt bar; Refine disabled until a saved design exists
- [x] Summary banner above the prompt bar; auto-clears when the user types; ✕ to dismiss
- [x] React Testing Library + happy-dom configured for frontend RTL tests
- [x] 17 backend refinement service tests + 3 endpoint tests; 3 new frontend RTL tests
- [x] `npx tsc --noEmit` passes with zero errors

### Sprint 9A — Version History & Restore ✅ Complete

- [x] `GET /api/design/version/{version_id}` — fetches a single DesignVersion; 401 / 403 / 404 guarded
- [x] `designId` / `designVersionId` keys stripped from `layout_json` before spread to avoid kwarg collision
- [x] 3 new backend tests (correct layout returned, 403 wrong user, 404 missing)
- [x] `fetchVersion(versionId)` exported from `design.service.ts`
- [x] `VersionHistoryDrawer` component — overlay drawer with version list, type badges, relative timestamps, per-row Restore
- [x] Restore loads the historical layout into the canvas as unsaved changes (user must Save to persist)
- [x] Per-row loading state — only the clicked Restore button shows "Restoring…"
- [x] `isMounted` ref guards setState calls against unmount in handleRestore
- [x] 2 RTL tests for VersionHistoryDrawer (renders rows, Restore calls API + closes drawer)
- [x] 2 Project page tests (History button opens drawer, close button closes it)
- [x] "History" button in project top bar opens the drawer
- [x] `npx tsc --noEmit` passes with zero errors

### Sprint 9B — Activity Log Panel ✅ Complete

- [x] Alembic `006` adds nullable, indexed `project_id` to `activity_logs` (no FK — append-only audit)
- [x] `ActivityLog.project_id` declared on the model
- [x] `log_activity(db, user_id, action, project_id=None)` — all 7 existing call sites pass `project_id`
- [x] `log_activity` sets `timestamp=datetime.now(timezone.utc)` explicitly so SQLite tests can order entries within the same second
- [x] `GET /api/projects/{project_id}/activity` returns 50 newest entries, scoped to the project, newest-first
- [x] 401 / 403 / 404 guarded; cross-project isolation verified by test
- [x] `ActivityLogOut` schema added
- [x] 3 new backend tests (scoped + ordered, 403 wrong user, isolation between projects)
- [x] `formatRelative` extracted to `frontend/src/utils/time.ts`; both drawers import from there
- [x] `projectService.activity()` + `ActivityEntry` type
- [x] `ActivityDrawer` component (mirrors VersionHistoryDrawer structure, action label map, `isMounted` ref)
- [x] 2 RTL tests for `ActivityDrawer` (rows with labels, empty state)
- [x] "Activity" button next to "History" in project top bar
- [x] 1 new Project page test (Activity button opens the drawer)
- [x] `npx tsc --noEmit` clean

### Sprint 9C — Auto-save with Drafts ✅ Complete

- [x] Task 1: Backend draft endpoint tests
  - Tests cover authenticated draft save, draft fetch, no-draft response, wrong-user access, layout JSON persistence, and named-version safety
- [x] Task 2: Backend draft service functions
- [x] Task 3: Backend draft schemas and endpoints
- [x] Task 4: Backend tests and backend draft verification
- [x] Task 5: Canvas store draft state
- [x] Task 6: Frontend draft service functions
- [x] Task 7: `useAutoSave` hook and tests
- [x] Task 8: Draft recovery in ProjectPage and recovery banner
- [x] Task 9: EditorToolbar draft indicator
- [x] Task 10: RTL tests for recovery banner
- [x] Task 11: Final checks and commit
- [x] Auto-save writes separate `auto_draft` versions without overwriting named/manual version history
- [x] Draft recovery banner lets users restore unsaved draft work into the editor before manually saving
- [x] EditorToolbar shows draft dirty, saving, saved, and error states
- [x] Backend and frontend checks pass

### Sprint 9D — Team Collaboration (Workspaces) ✅ Complete

- [x] Task 1: Sprint 9D workspace collaboration plan
- [x] Task 2: Backend workspace/team tests
- [x] Task 3: Workspace and TeamMember models/migration
- [x] Task 4: Backend workspace services
- [x] Task 5: Workspace API endpoints
- [x] Task 6: Project-workspace association and access checks
- [x] Task 7: Frontend workspace service functions
- [x] Task 8: Basic workspace dashboard UI
- [x] Task 9: Member management UI
- [x] Task 10: Permissions and activity log polish
- [x] Task 11: Final checks and Sprint 9D completion update
- [x] Workspaces support owner, admin, editor, and viewer roles with backend-enforced permissions
- [x] Existing users can be added by email and shared workspace projects remain compatible with personal projects
- [x] Workspace activity history includes team actions and shared project/design changes
- [x] Backend tests, frontend tests, typecheck, production build, migration, and live PostgreSQL API smoke flow pass

Deferred beyond Sprint 9D:
- Real-time collaboration
- Pending email invitations / actual email sending
- Comments
- Notifications
- Workspace billing

### Sprint 10 — Web Scraper and Data Pipeline ✅ Complete

- [x] Task 1: Sprint 10 scraper/data-pipeline plan
- [x] Task 2: Backend scraper pipeline tests
- [x] Task 3: ScraperSource and ScraperRun models/migration
- [x] Task 4: RobotsTxtChecker utility
- [x] Task 5: Basic safe-source scraper runner
- [x] Task 6: Data cleaning and deterministic metadata extraction
- [x] Task 7: Structured LayoutPattern model/migration
- [x] Task 8: Scraper management API endpoints
- [x] Task 9: Scraper monitoring UI
- [x] Task 10: Final checks and Sprint 10 completion update
- [x] Pipeline collects permitted public textual layout references only and stores source URL plus access timestamp provenance
- [x] Every scrape run checks `robots.txt`; blocked or unreachable policy checks fail closed without fetching source content
- [x] Raw text records and deterministic `LayoutPattern` metadata remain isolated from design generation
- [x] Authenticated scraper APIs and the Data Pipeline monitoring UI cover source management, explicit runs, status, history, and extracted patterns
- [x] Backend tests, frontend tests, typecheck, production build, PostgreSQL migrations, and local API smoke flow pass

Deferred beyond Sprint 10:
- AI training and layout-generation improvements belong to Sprint 11
- Scheduled/background crawling and crawl queues
- Dedicated system-admin authorization for pipeline management
- Source-specific extraction adapters

Intentionally excluded:
- Scraping or storing copyrighted floor-plan images
- Personal-data collection

### Sprint 11 — Layout Improvement Using Pattern Data ✅ Complete

- [x] Task 1: Sprint 11 layout-improvement plan/spec
- [x] Task 2: Benchmark prompt and quality tests
- [x] Task 3: Layout-pattern access service with fallbacks
- [x] Task 4: Room-sizing rule improvements
- [x] Task 5: Zoning and adjacency improvements
- [x] Task 6: Building-type layout templates
- [x] Task 7: Prompt requirement extraction improvements
- [x] Task 8: Layout-quality scoring
- [x] Task 9: Minimal generation-insight UI
- [x] Task 10: Future-AI placeholder documentation
- [x] Task 11: Final checks and Sprint 11 completion update
- [x] Deterministic generation uses structured pattern data when available and realistic fallback rules when the database has no matching patterns
- [x] Room sizing, zones, adjacency ordering, prompt extraction, building templates, multi-floor compatibility, and quality scoring improve concept layouts without external model calls
- [x] Editor layout insights show detected building type, applied template, zones, quality score, and compact diagnostics
- [x] Backend tests, frontend tests, typecheck, production build, and migration-head checks pass

Deferred beyond Sprint 11:
- Paid AI API integration
- OpenAI, Claude, or Gemini provider integration
- Local model integration
- Full AI model training or fine-tuning
- LLM-based layout generation
- Advanced architectural validation
- Automatic self-learning from user edits
- Complex spatial optimization algorithms
- CAD/BIM reasoning

### Sprint 12 — Export, Share, and Polish ✅ Complete

- [x] Task 0: Clean `CLAUDE.md` development-rule formatting
- [x] Task 1: Sprint 12 export/share/polish plan and checklist
- [x] Task 2: Backend export/share tests
- [x] Task 3: Backend export/share models and services
- [x] Task 4: Backend export/share API endpoints
- [x] Task 5: Frontend image export
- [x] Task 6: Frontend PDF export
- [x] Task 7: Shareable read-only project links
- [x] Task 8: Export/share activity labels and integration
- [x] Task 9: MVP user-interface polish
- [x] Task 10: Full local MVP smoke testing and fixes
- [x] Task 11: README and deployment readiness
- [x] Task 12: Final checks and Sprint 12 completion update

- [x] `CLAUDE.md` Development Rules cleanup completed
- [x] Image export downloads the current canvas and records project activity
- [x] PDF export produces a lightweight project summary and records project activity
- [x] Share links open a public read-only latest-saved-layout view and can be revoked
- [x] Export/share actions are permission-safe and readable in activity history
- [x] Core MVP UI polish and local smoke verification completed
- [x] README, Docker, migrations, setup, and deployment-readiness notes updated
- [x] Backend tests, frontend tests, typecheck, production build, production dependency audit, Docker image builds, and healthy Compose startup pass

Deferred beyond Sprint 12:
- CAD/BIM export
- Real-time collaboration
- Public template marketplace
- Payment/subscription system
- Advanced deployment automation
- Mobile/tablet-specific UI
- Advanced PDF styling/report templates
- Cloud file storage for exports

### Sprint 13 — Smarter Layouts, Pattern Learning, and Better Canvas ✅ Complete

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

- [x] Sprint 13 implementation plan created at `docs/superpowers/plans/2026-06-07-sprint13-smarter-layouts-pattern-canvas.md`
- [x] Pattern data validation keeps low-quality scraped data from influencing generation
- [x] Normalized pattern vocabulary maps messy scraped terms to internal room/building types
- [x] Pattern-weighted generation improves room sizes, zones, adjacency, and layout metadata without paid AI APIs
- [x] Canvas visualization improves readability while preserving editing, save, export, and share behavior
- [x] Non-AI pattern data workflow documented at `docs/PATTERN_DATA_WORKFLOW.md`
- [x] Backend tests, frontend typecheck, production build, and frontend tests pass

Deferred beyond Sprint 13:
- Paid AI API integration
- OpenAI, Claude, Gemini, or local model integration
- AI model training or fine-tuning
- CAD/BIM export and structural validation
- Advanced spatial optimization
- Public scraper/source-management workflow for normal users

### Sprint 14 — Advanced Deterministic Prompt Parser ✅ Complete

- [x] Stage 1: Normaliser and synonym expansion
- [x] Stage 2: Building type inference with BHK support
- [x] Stage 3: Compound room extraction
- [x] Stage 4: Merge and deduplication
- [x] Stage 5: Relational constraint extraction
- [x] Stage 6: Size and proportion resolver
- [x] Stage 7: Wire parser stages into `prompt_service.py`
- [x] Stage 8: Update `layout_service.py` for parser-aware adjacency and floor distribution
- [x] Stage 9: Optional Vastu compliance module and integration
- [x] Stage 10: Full parser/layout regression suite and final Sprint 14 completion update

- [x] Parser work is on feature branch `sprint-14/advanced-keyword-parser`
- [x] All 10 stages committed as separate workflow units
- [x] Full parser + regression suite passes (`377 passed`)
- [x] Advanced parser (`parse_prompt`) is wired into production generation via `designs/router.py`
- [x] Vastu compliance is opt-in (triggered by "vastu"/"vaastu" keywords only)
- [x] All existing tests continue to pass — zero regressions

Deferred beyond current Sprint 14 partial scope:
- Paid AI API integration
- AI model training or fine-tuning
- Full CAD/BIM reasoning
- Complex structural validation
- Automatic self-learning from user edits

### Sprint 15 — Layout Quality, Visual Improvements & Overlap Fix ✅ Complete

- [x] Multi-pass iterative overlap repair in `_repair_rooms` (resolves X and Z direction overlaps; up to 10 passes until stable)
- [x] Stair placement made relative to `x_offset` — no longer hardcoded at (1.0, 1.5)
- [x] Partition wall generation: `_generate_partition_walls` creates thin wall meshes between every adjacent room pair on a floor
- [x] Quality scorer: `dining_room` added to expected apartment/house rooms — pure 3BHK no longer trivially scores 100/100
- [x] Quality scorer: building-type completeness check with per-type expected room sets
- [x] Quality scorer: adjacency density check penalizes layouts with very low satisfaction rates
- [x] Scene.tsx: floor slabs thicker (0.45m in 3D vs 0.16m), distinct per-floor color palette, ceiling plane between stories in multi-floor 3D view
- [x] RoomMesh.tsx: edge outlines rendered on all room/stair objects (not just selected) so adjacent rooms have visible separation; wall/partition opacity increased to 0.62
- [x] 17 new Sprint 15 tests covering overlap repair, no-overlap guarantee for 5-bed 2-story layout, partition wall presence, quality penalties
- [x] 394 backend tests passing, zero regressions; frontend typecheck clean

Deferred beyond Sprint 15:
- True internal wall topology (shared-wall detection, door openings in walls)
- Floor plan 2D rendering mode with dimension labels
- Room labeling on floor plan (room names at centroid in plan view)
- Refine improvements (prompt understanding, adjacency-aware refinement)
- Per-room activity log API

### Sprint 15 Phase 2 — Tiled Floor-Plan Algorithm ✅ Complete

- [x] `_tile_rooms` zones rooms into front/corridor/back rows; each row scales to fill the exact building width so rooms share walls (zero gaps), replacing the old row-based algorithm that left "floating box" gaps
- [x] `_fill_row` scales room widths proportionally to fill `building_width` exactly
- [x] Residential building types (`apartment`, `house`, `studio`, `two_storey_home`, `bungalow`, `villa`, `townhouse`) route through `_tile_rooms`; commercial types continue using `_place_rooms`
- [x] Multi-floor tiled layouts pre-compute a shared `target_width` from the widest floor so all storeys align on the same building width
- [x] Stairs reserve a 2.2m strip on the building's right edge, using the shared `target_width` so stair position is consistent across all floors even when some floors have no other rooms
- [x] `_assign_rooms_to_floors`: every floor with bedrooms now also gets its own bathroom
- [x] `generate_layout` produces a single candidate for tiled types instead of 3 variants
- [x] `_outside_footprint` and overlap checks gain a 2cm epsilon to absorb float drift at shared walls without masking real overlaps
- [x] Quality scorer no longer double-counts symmetric avoid-adjacency violations (e.g. kitchen/bathroom)
- [x] New tiled-layout regression suite (`test_sprint15_tiled_layout.py`) plus updated benchmark/unit test expectations
- [x] 409 backend tests passing, zero regressions

Deferred beyond Sprint 15 Phase 2:
- True internal wall topology (shared-wall detection, door openings in walls)
- Floor plan 2D rendering mode with dimension labels
- Room labeling on floor plan (room names at centroid in plan view)
- Refine improvements (prompt understanding, adjacency-aware refinement)
- Per-room activity log API

### Sprint 16 — Unified Space-Filling Layouts & Adjacency Reasoning ✅ Complete

> Full spec: [`docs/superpowers/specs/2026-06-11-sprint16-unified-space-filling-layouts.md`](docs/superpowers/specs/2026-06-11-sprint16-unified-space-filling-layouts.md)
> Branch: `sprint-16/unified-space-filling-layouts` (off `main`). Scope: **Phases 1–3**, plus two unplanned parser/NLU fixes (Gaps A & B) found via user testing.

**Why:** `layout_service.py` had two placement engines. Residential types used the good space-filling tiler (`_tile_rooms`, zero gaps). Everything else (office, clinic, retail, restaurant, school, classroom, and mixed-vocab prompts resolving to a commercial `building_type`) used the old row-band engine (`_place_rooms`), whose footprint was the bounding box of mismatched-width zone rows — the source of large "blank space" inside the boundary walls. The tiler also ignored the parser's adjacency constraints and used one uniform depth per row, distorting proportions.

- [x] **Phase 1 — Unify on the tiler:** `_TILED_BUILDING_TYPES` now covers both the production `detect_building_type` vocabulary (8 types) and the parser's `infer_building_type` vocabulary (13 types) — office, clinic, restaurant, retail, classroom, school, hotel all tile with zero gaps; `_place_rooms`/`_repair_rooms` remain a fallback only.
- [x] **Phase 2 — Real adjacency reasoning:** `_chain_by_adjacency`/`_order_zone_rooms` thread the parser's MUST/SHOULD `AdjacencyConstraint`s into row ordering inside `_tile_rooms`; `interleave_service` attaches a bathroom/ensuite to the bedroom it's constrained to (with ensuite→bathroom aliasing).
- [x] **Phase 3 — Proportion realism:** `_fill_row` rewritten to allocate row width proportional to each room's target *area* (not pre-sized width), so large rooms (e.g. open workspace) get proportionate space instead of being squeezed by neighbors — this also fixed the last failing adjacency benchmark.
- [x] **Geometry fixes:** boundary walls offset outward by half thickness (rooms no longer overlap the walls bounding them); implicit privacy corridor gated to residential types + clinic (clinics have a real circulation corridor); commercial multi-floor distribution (`_assign_commercial_floors`) round-robins rooms evenly across floors and anchors public rooms to the ground floor, fixing near-empty ground floors for types like `school`.
- [x] **Gap A — missing building templates:** `infer_template_rooms` was silently falling back to the apartment template (bedrooms/kitchen/living room) for any of 6 building types with no template entry — this directly caused the user-reported "clinic generates bedrooms" bug. Added proper templates for `clinic`, `school`, `hotel`, `villa`, `townhouse`, `warehouse`.
- [x] **Gap B — NL synonyms & relational patterns:** added missing synonyms ("seating area"/"waiting area"→`waiting_room`, "doctor's office"/"exam room"/"treatment room"→`consultation_room`); generalized the adjacency regex to handle directional phrasing (behind, opens into, leads to, opposite, facing, backs onto) and reversed sentence order ("next to X is Y"), with filler-word tolerance.
- [x] New `test_sprint16_unified_layouts.py` (21 tests: footprint utilization, no-overlap, key adjacencies, relational-language adjacency, multi-floor commercial sharing, clinic/school template correctness, NL synonym resolution); updated `test_layout_architectural_rules.py`, `test_layout_benchmarks.py`, `test_sprint15_tiled_layout.py` for the new tiled-commercial semantics
- [x] Full backend suite green (430 passed, 0 failed); `npx tsc --noEmit` clean

Known limitation (not fixed, flagged for later): relational phrases with an inserted clause between the two room mentions (e.g. "entry door **which** opens into the reception area") still fail to match the adjacency extractor.

Deferred beyond Sprint 16:
- Phase 4: quality-scorer space-utilization metric + parser-tied adjacency-satisfaction score (so the generator self-selects good layouts)
- Phase 5: 2D floor-plan view mode, door openings punched into partition walls, persistent room-type color legend
- True internal wall topology (shared-wall dedup, openings)
- Paid AI / model-based generation, CAD/BIM, structural validation

### Sprint 17+ — 10× Master-Brief Vertical Slice ✅ Phases 0–3 complete (2026-07)

> A second, independent pass on the 10x roadmap driven by the master
> implementation brief. **Do not confuse these Phase numbers with the older
> "Sprint 17 Phase 0–4" DesignParams/dimensions numbering below** — this is a
> separate initiative delivered as four focused branches off `main`'s current
> tip (`sprint-17/phase0-design-params`), one per concern (per the user's
> branch-per-task preference). None pushed yet (local only until asked).

- **Phase 0 — Security & hardening** (`sprint-17/phase0-security-hardening`, 2 commits): scraper is admin-only (`User.is_admin`, mig 012); `utils/ssrf.py` blocks private/loopback/link-local/metadata targets (v4+v6, per-redirect); access tokens cut 7d→45m with `jti`/`type`, revocable refresh tokens (mig 013, `POST /auth/refresh` rotation, `/logout` revoke); `utils/rate_limit.py` per-user/IP limiter; prompt/layout/body payload caps; env-driven `ENV`/`ALLOWED_ORIGINS` + security headers + prod SECRET_KEY gate. 512 backend tests.
- **Phase 1 — Canvas direct-manipulation** (`sprint-17/phase1-canvas-ux`): footprint-clamped drag, 8-point `ResizeHandles` (min-dim + single log entry), click-to-place, 6 new object types (corridor/lift/shaft/furniture/column/generic), `MeasurePanel` + tape tool, bounded undo/redo + Cmd/Ctrl+Z. 106 frontend tests, tsc + build clean.
- **Phase 2 — ProgramGraph** (`sprint-17/phase2-program-graph`): `backend/app/services/planning/` — building-type-agnostic typed Node/Edge graph + adapters (`from_parser_output`/`from_building_template`/`from_user_objects`/`merge`) + lossless `to_room_specs`/`from_room_specs` bridge + explainable `validate()`. Additive: golden tests pin byte-identical layout vs. the direct path across residential + office/clinic/warehouse/restaurant. 493 backend tests.
- **Phase 3 — Billing & entitlements** (`sprint-17/phase3-billing`, stacked on Phase 0): Plan/Subscription/PaymentOrder/PaymentEvent/Entitlement/UsageCounter (mig 014); `entitlement_service` (backend-verified free-tier limits, feature gates → 402/403, metered generations, admin bypass); `billing_service` (Razorpay order via httpx, signature-verified idempotent webhook, no SDK); `/api/billing/*`; gates wired into project-create + generate. No card/bank/UPI/PAN stored. 520 backend tests.

New reference docs: [`docs/NON_ML_GRAPH_LAYOUT_ENGINE.md`](docs/NON_ML_GRAPH_LAYOUT_ENGINE.md), [`docs/SAAS_HARDENING_AND_MONETIZATION.md`](docs/SAAS_HARDENING_AND_MONETIZATION.md), [`docs/EXPORT_AND_BIM_ROADMAP.md`](docs/EXPORT_AND_BIM_ROADMAP.md), [`docs/HYPAR_INSPIRED_PRODUCT_STRATEGY.md`](docs/HYPAR_INSPIRED_PRODUCT_STRATEGY.md).

Hard constraints held throughout: no ML / no paid-AI layout generation; every change additive and backward-compatible with the existing layout JSON + `RoomSpec → generate_layout` path; no new runtime dependencies (rate-limiter and Razorpay both stdlib). Migration chain across branches is linear (Phase 0 adds 012+013, Phase 3 adds 014 on top; Phases 1–2 add none), so merge order is Phase 1 & Phase 2 (independent, off base) then Phase 3 (brings Phase 0). Deferred: graph-driven placement (Phase 4), circulation/doors (Phase 5), furniture (Phase 6), CAD/BIM export (Phases 7–8), frontend token→cookie migration, full cross-user authz matrix.

### Sprint 17+ — 10× Roadmap 🚧 In Progress (Phases 0-3 core complete, Phase 4 underway)

> Full roadmap: [`docs/superpowers/plans/2026-06-22-10x-roadmap.md`](docs/superpowers/plans/2026-06-22-10x-roadmap.md)
> Branches: `sprint-17/dimensions-on-canvas` (Phase 1, off `main`), `sprint-17/phase0-design-params` (Phase 0 + Phase 2 + Phase 3 + Phase 4, stacked on top of it). Neither is pushed yet — this machine's GitHub credentials (`udai-shunya`) lack write access to `samarth080/archiai-saas`; push once that's resolved.

A longer-horizon plan to move from "concept layout MVP" to a standout product, reverse-engineered from Hypar's parametric-generative approach. Five pillars, sequenced into phases:

- **Pillar A — Real planning engine:** replace row/tile packing with a BSP/slicing-tree space partitioner for a true building envelope, plus a real circulation graph, doors on the path, and orientation-aware windows.
- **Pillar B — Dimensions & interaction:** on-canvas dimension lines + area badges on click/select (not just the Inspector side panel), a metrics HUD, CAD-lite snapping.
- **Pillar C — Data learning:** swap the scraper's fetcher to Scrapling (handles JS/anti-bot sites like ArchDaily/Dezeen), extract structured project data (not just visible text), aggregate into statistical priors (area distributions, adjacency probabilities) feeding the existing `LayoutPatternRules` pipe.
- **Pillar D — UI/UX overhaul:** single-screen layout (brief/params, canvas + option gallery, inspector/metrics), muted architectural palette, option gallery for generated candidates, command palette, dimensioned plan-view rendering with door swings.
- **Pillar E — Interop & hardening:** SVG/DXF/glTF export, production frontend build (currently Docker serves the Vite dev server), refresh-token auth hardening.
- **Pillar F — 3D modeling fidelity (not started, broadly scoped):** rooms currently render as flat-colored boxes with no real wall/door/window geometry (doors and windows are thin marker boxes, not openings cut into a wall), no furniture, no materials/textures, and no roof or exterior facade detail — multi-floor buildings are just stacked flat slabs. Flagged by the user as a real gap; not broken down into phases yet, revisit once Phase 4's UI/export work lands.

Phased rollout: Phase 0 (pipeline refactor + `DesignParams`) → Phase 1 (dimensions + UI shell) → Phase 2 (BSP planning engine + circulation) → Phase 3 (Scrapling + priors) → Phase 4 (optioneering + export) → Phase 5 (optional ML + IFC, later). Pillar F isn't yet slotted into a phase.

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
- [x] **Bug fix:** the global toggle rendered dimension lines for every room in *any* view mode, including the default 3D perspective camera — each line's fixed 0.45m offset landed inside neighbouring rows in a tightly tiled plan, so multiple rooms' labels piled on top of each other (this is what produced the cluttered screenshot during testing). Now restricted to plan/top view, where the convention actually reads cleanly; the selected room's own dimensions still show in any view mode.
- [ ] Hover-triggered dimensions on non-selected rooms (deferred — click/select only for now)
- [ ] Rotation-aware dimension lines (current lines assume axis-aligned rooms)
- [ ] `sq ft` unit toggle on the area badge

**Phase 2 progress (BSP space partitioner + real circulation) ✅ Core deliverables complete:**
- [x] Every partition wall between two adjacent rooms whose shared span is >= 1.2m gets a door marker centred on it (`_generate_partition_walls`), so generated floor plans are walkable room-to-room instead of solid-walled boxes with only one entry door total
- [x] **Bug fix — wrong adjacency branch:** when one room's footprint was narrower than and fully nested inside another's span on one axis (e.g. an Office nested inside a wider Hallway), both gap measurements read near-zero and the code picked the wrong wall orientation, so Hallway↔room walls/doors were silently never generated at all. Fixed by comparing real overlap magnitude on each axis instead of relying on which gap happened to read near zero.
- [x] **Bug fix — doors routed wrong:** even with the geometry fixed, every adjacent pair got a direct door unconditionally, so two private/service cells sitting side by side (e.g. Office next to Bathroom) each got a lateral door to each other instead of each opening onto the corridor. `_wants_direct_door` now gates this: the corridor always connects to whatever it touches, open-plan public rooms still connect directly to each other, but two private/service cells only get a direct door when there's no corridor on the floor to route through instead. This was the exact bug visible in the user-reported clinic screenshot (Office<->Bathroom and Bathroom<->Consultation Room doors, but nothing connecting either to the Hallway).
- [x] **Real BSP space partitioner:** `_bsp_partition_rect` is a true 2D recursive partition — `_fill_row` (the plain tiler) only ever varies room WIDTH within a band, forcing every room in that band to the SAME depth; BSP can cut a rectangle along either axis (always the currently-longer side, split point chosen by cumulative room area), so a deep bedroom and a shallow bathroom sharing a row can each get the depth their area actually calls for, while still fully tiling the rectangle with zero gaps
- [x] **Competes, doesn't replace:** tiled building types now generate two full candidates per request (`placement_style` "tile" and "bsp"), both scored by the existing quality scorer, higher score wins — the same `max()` competition the codebase already used for row-offset variants. BSP can never make a layout worse, only take over when it demonstrably produces better proportions. Winning engine recorded in `metadata.placementEngine`.
- [x] **Real circulation check:** `_floor_unreachable_rooms` builds a per-floor graph from interior doors and walks it from the floor's entry point (the `entry`-typed room on the ground floor, or the room nearest the stairs on upper floors), flagging by label any room not actually reachable — not just "are there doors" but "can you walk from the entry to every room." Penalises the quality score and surfaces as a warning + suggestion.
- [x] Tests cover door placement, span-matching, the 1.2m minimum-span cutoff, the corridor-routing fix (regression test against the exact clinic layout that surfaced the bug), open-plan rooms still connecting directly, BSP's zero-gap/zero-overlap tiling guarantee, BSP producing genuinely variable depths under heterogeneous room areas, candidate competition never scoring below either engine alone, and reachability correctly flagging a deliberately disconnected room
- [x] **Bug fix — dropped metadata fields:** found a second instance of the dropped-field bug from Phase 0 (`FloorResponse.footprint`) — `GenerateMetadata` never declared `candidateCount`, so it was silently stripped from every API response by the response model the whole time. Fixed alongside adding `placementEngine`.
- [x] `layout_service.py` given a module docstring + section banners (comments only, zero logic change) documenting the two-engine history, since that's exactly the kind of file where a bug like the corridor-nesting one hides
- [ ] Door-clearance checks (a clearance rectangle in front of each door, flagged if another room/object overlaps it) are not implemented — the roadmap's stretch goal for this phase, lower priority than the partitioner and circulation work above
- [ ] BSP is currently only used for the back/private+service row; the front row (open-plan living/kitchen/dining) deliberately still uses uniform-depth `_fill_row` since a benchmark test asserts those rooms share an exact Z position — revisit if BSP's depth-variance benefit is wanted there too

**Phase 3 progress (Scrapling + data priors) ✅ Core deliverables complete:**
- [x] **Scrapling fetcher swap:** `fetch_public_page` now tries Scrapling's `AsyncFetcher` first (fast, no browser, curl_cffi-based — handles the common case and basic bot checks via TLS/header fingerprinting), escalating to `StealthyFetcher` (a real stealthy browser session) only when the plain fetch comes back blocked (403/429/503) or the body shows a captcha/block-page marker. Installed from `github.com/D4Vinci/Scrapling` (explicit instruction, not the PyPI release), pinned to the resolved commit in `requirements.txt`. `StealthyFetcher`'s browser binaries need `scrapling install` as a deployment step — not run in this environment and not needed for tests or the plain-fetch path; the import is guarded so a missing browser install degrades to skipping escalation rather than crashing the scraper.
- [x] **Real statistical aggregation:** `get_layout_pattern_rules` previously picked exactly one `LayoutPattern` row per room type (highest confidence, most recent) and discarded every other usable row — scraping ten sites for "bedroom" area only ever used one of them. `_select_best_tier_patterns` + `_aggregate_patterns_for_room` now combine every pattern in the winning confidence tier: area ranges use the median across sources (robust to outliers), adjacency only keeps pairs corroborated by a real fraction of sources once there are enough to be picky about. The existing trust hierarchy is preserved exactly — a single high-confidence source still beats a pile of seed rows outright (a prior test pins this down); aggregation only kicks in *within* the winning tier.
- [x] `applied_pattern_count` now honestly counts every pattern that fed the aggregate, not just one per room type
- [x] Tests cover the escalation/blocked-detection logic directly (mocking at the `AsyncFetcher`/`StealthyFetcher` boundary, not `fetch_public_page` itself, since the rest of the scraper suite monkeypatches that wholesale), median aggregation across disagreeing sources, the adjacency support threshold, and single-source mentions still counting without corroboration
- [ ] The roadmap's bigger structured-extraction piece — a new `ScrapedProject` table, a real Spider crawler, and project-level fields (full room lists with per-room areas, plan descriptors) beyond the existing per-sentence `LayoutPattern` extraction — is not started. The aggregation pipe above already operates on the existing `LayoutPattern` table; a richer source table would feed it more (and better) data but isn't required for the aggregation logic itself to work
- [ ] Scheduled/background crawling, crawl queues, and the public scraper/source-management workflow for normal users remain out of scope (carried over from Sprint 10's deferred list)

**Phase 4 progress (Pillar D started — option gallery + muted palette):**
- [x] **Option gallery:** `generate_layout` already built 2-3 full candidate layouts per request (tile vs bsp for tiled types, x-offset variants for the row-band fallback) and discarded everything but the winner. `generate_layout` gained a `return_all_candidates` flag (default off, every existing call site unaffected); `/api/design/generate` now returns the losers as `alternatives` — never persisted, since only the winner is saved as the Design/DesignVersion. New `OptionGallery.tsx` renders a compact card per alternative (score, engine, room count, area) below the insights panel; clicking one swaps it into the canvas (`loadLayout` + `markDirty`, since picking an alternative doesn't auto-save it).
- [x] **Muted architectural palette:** `ROOM_COLORS` (backend) and `OBJECT_DEFAULTS`/`INITIAL_ROOMS` (frontend) were raw bright Tailwind 400/500 swatches — a "toy blocks" look. Every value is now that same hex run through one fixed HSL transform (saturation ×0.62, lightness +0.07), so the palette stays internally consistent (same relative hues/distinguishability) while reading as a muted architectural drawing instead of candy UI. `wall` deliberately untouched (structural marker, not a room identity color).
- [x] **Single-screen layout already satisfied:** checked the existing Project page structure before planning new work — canvas, Inspector, EditorToolbar, MetricsHud, prompt bar with collapsible plot params, and now the option gallery are already all on one screen with no route hops. Pillar D's "single-screen layout" ask needed no new work.
- [ ] Command palette (⌘K) — not started
- [ ] Dimensioned plan-view rendering with door swings — not started (door geometry itself is a Pillar F gap, see below)
- [ ] Parameter-sweep optioneering to get 6-12 candidates instead of the current 2-3 — not started; the gallery infrastructure is ready for it whenever the candidate count grows
- [ ] Pillar E (SVG/DXF/glTF export, production frontend build) — not started

Not yet started: the rest of Phase 4 (command palette, plan-view door swings, parameter-sweep optioneering, Pillar E export/hardening), Phase 5 (optional ML/IFC), Pillar F (3D modeling fidelity — see the roadmap doc's section 7a, flagged by the user but not yet phased).

### Sprint 18 — Master-brief roadmap continued 🚧 (new sprint line; Sprint 17 was getting overloaded)

> Per the user, further master-brief roadmap work moves to `sprint-18/...` branches rather than piling onto Sprint 17.

**Phase 4 (graph-driven layout)** (`sprint-18/phase4-graph-scoring`, off `sprint-17/phase2-program-graph` since it needs the ProgramGraph):

- *Slice 1 — graph-satisfaction scoring:* `planning/graph_scoring.py` measures how well a *generated* layout honours its ProgramGraph's MUST/SHOULD `adjacent` edges — deterministic AABB shared-wall geometry, weighted score, and the human-readable list of unmet MUST adjacencies. Wired additively into `/api/design/generate` as `metadata.graphSatisfaction` (schema field added so it isn't dropped).
- *Slice 2 — graph-aware candidate selection:* `generate_layout` already builds several candidates (tile/bsp/x-offset variants) and kept the highest quality score. Among the tiler/BSP candidates the winner key is now `(quality_score, adjacency_bonus)` — quality stays primary, adjacency realised breaks ties.
- *Slice 3 — a real graph-driven placement engine:* `_graph_pack_rooms` is a genuinely new engine (not a re-rank): the zone tiler honours adjacency only *within* a front/back row, so a MUST pair split across zones can never share a wall. The graph packer orders the **whole** room set by the adjacency graph (MUST-linked rooms consecutive, regardless of zone) and flows them into width-filling rows, keeping a MUST pair in one row — realising cross-zone adjacencies the tiler structurally can't, still zero-gap. It's added as an **extra competing candidate only when hard MUST constraints exist**, and it **replaces the tiler winner only when it realises strictly more MUST adjacencies at no quality cost** (a guaranteed improvement, never a quality regression). Demonstrated: `clinic where the reception is next to the consultation room` → tiler MUST 0/1 (q81), graph MUST 1/1 (q86), graph wins.

No existing candidate is generated differently and none removed. 18 new tests total; full backend suite 509 passed, zero regressions.

Deferred (Phase 4 remainder): richer graph-driven placement honouring `preferred_relative_position`/`requires_external_wall` and true BSP footprint slicing by adjacency cluster (the current packer clusters into rows). The scoring + selection + row-clustering engine land first; the full spatial solver is the larger follow-up.

### Sprint 19 - Release A: Safe Editor Interaction, Component Parity, and Progressive Editing Foundation

- [x] **Central component registry:** frontend component behavior now comes from `componentRegistry.ts` for all supported types: room, wall, door, window, stair, floor, open_space, corridor, lift, shaft, furniture, column, generic. The registry owns labels, defaults, create/select/move/resize/rotate policies, minimum dimensions, beginner/professional palette placement, inspector policy, and rendering treatment.
- [x] **Floor object policy:** `CanvasFloor` remains the level/floor concept; `objectType: "floor"` remains a legacy editable canvas object with explicit full lifecycle support instead of being silently dropped or converted.
- [x] **Safe selection and movement:** first left click on an unselected object selects only. Moving requires pressing an already selected object and crossing a 6px screen-space threshold. Active move uses transient store updates and commits one final history/activity/autosave action on release; pointer cancel/Escape restore a safe idle state.
- [x] **Navigation rules:** left mouse is reserved for selection/editing, right drag pans, wheel zooms, and middle drag orbits only in 3D. Context-menu prevention is scoped to the canvas container.
- [x] **Resize parity:** selected resizable objects show plan/top-view handles. Resize preserves type-specific minimums, floor elevation, footprint clamping, transient updates, and a single final history entry.
- [x] **Clipboard and history:** Ctrl/Cmd+C, Ctrl/Cmd+V, Ctrl/Cmd+Z, Ctrl/Cmd+Shift+Z, Ctrl+Y, Ctrl/Cmd+D, Delete/Backspace, and Escape share editable-target protection. Internal clipboard paste regenerates ids, targets the active floor, offsets progressively, selects the pasted object, and supports undo/redo.
- [x] **Inspector and ToolRail parity:** Inspector type options and field policies are registry-driven. Beginner tools show common components; More components exposes open space, lift, shaft, generic object, and legacy floor object.
- [x] **Persistence compatibility:** frontend serialization preserves all valid component types. Backend regression coverage verifies all 13 component types survive save, latest reload, version fetch, and public share.
- [x] **Verification:** frontend tests 120 passed, frontend TypeScript check passed, frontend production build passed, backend tests 551 passed. Local backend (`127.0.0.1:8000`) and frontend (`127.0.0.1:5173`) server smoke checks returned 200.
- [ ] **Manual browser acceptance:** visual in-app browser verification was blocked in this Codex session because no browser backend was available (`agent.browsers.list()` returned `[]`). The servers were started and healthy; complete visual beginner/professional acceptance remains pending in an environment with browser control.

### Sprint 20 - Reliable Sessions, Save Safety, and CI Protection

- [x] **Refresh-token session continuity:** frontend auth state now persists both the short-lived access token and the refresh token returned by login/register. Startup keeps the user authenticated when only the access token has expired and a refresh token remains valid, so the next protected request can refresh instead of immediately clearing the session.
- [x] **Single-flight Axios refresh flow:** protected 401 responses now share one in-flight `/api/auth/refresh` request, wait for rotation to finish, then retry each eligible original request once with the new access token. Auth endpoints, requests marked `skipAuthRefresh`, already-retried requests, and non-401 errors do not enter the refresh path.
- [x] **Safe failure behavior:** refresh failure clears auth state and redirects to `/login`; 403 authorization failures, 422 validation failures, 429 rate limits, 402 entitlement/usage limits, network failures, and backend 5xx responses surface through the caller without being treated as logout.
- [x] **Save/draft integrity:** manual layout saves and auto-save drafts resolve as saved only after the retried request succeeds. Failed refresh leaves manual saves in `error` while preserving unsaved canvas state, and draft failures leave `draftStatus: "error"` with recoverable in-memory work. Regression tests pin that a manual save after token refresh creates only one named version write and that draft saves remain separate from named versions.
- [x] **CI protection:** `.github/workflows/ci.yml` added for pushes to `main` and pull requests. CI runs backend dependency install + `pytest`, then frontend `npm ci`, `npm test`, `npx tsc --noEmit`, and `npm run build` without deployment or secrets.
- [x] **Verification:** frontend tests 153 passed, frontend TypeScript check passed, frontend production build passed, backend tests 558 passed. Focused session-expiry simulations cover concurrent 401s, refresh success/failure, retry limits, non-refresh status codes, autosave, manual save, and local input preservation.
- [ ] **Live browser acceptance:** deterministic automated tests cover the Sprint 20 session-expiry scenario; full live browser acceptance with a running app session was not performed in this Codex environment.

### MVP Rework 🚧 — LLM-first pipeline per `ArchiAI_Implementation_Workflow_fable.md` (in-place, started 2026-07)

> The owner's MVP Implementation Workflow (prompt → **local LLM extraction** (LM Studio + Qwen3.5 9B on the host RTX 4060) → clarification → deterministic subdivision engine → quality+Vastu score → editable 2D SVG + the existing 3D editor with two-way sync → save/version → PNG/PDF/share/**IFC/DXF**) is being implemented **in place in this repo** (owner decision — not a greenfield sibling). Everything is additive: the legacy `parse_prompt → generate_layout` path, its 550+ tests, auth, workspaces, and billing remain untouched and green. Auth is KEPT (the workflow's "no accounts" was greenfield scope-cutting; ours is already built). Graph2Plan/fine-tuning/multi-candidate/native plugins stay excluded per the workflow.
>
> Key adaptation decisions: `LayoutPlan` (NW-origin, meters, walls/doors first-class, rotation ∈ {0,90,180,270}) is the MVP pipeline's canonical contract, with converters to the legacy center-based canvas JSON so the Sprint 19 editor renders it; **walls/doors are derived artifacts** regenerated deterministically from rooms after every edit; sizing table lives in `config/mvp_defaults.py` (not settings.py — env config vs product constants); branch-per-phase (`mvp/phaseN-*`).

- [x] **Phase 0 — env + locked contracts** (`mvp/phase0-contracts`): `schemas/requirements.py` (closed `RoomType` enum, StrictInt counts, string-number rejection, `extra="forbid"`, master_bedroom counting rule locked in the docstring), `schemas/layout_plan.py` (coordinate convention stated once), `schemas/quality_report.py`; `config/mvp_defaults.py` (9×12 m default plot, east default facing, 12-type room sizing table, public/private zoning sets); `frontend/src/types/contracts.ts` mirror; `/api/health` now reports `db` + `llm` separately (LLM down = feature-degraded, not app-down); `LLM_BASE_URL` setting + compose `extra_hosts: host.docker.internal:host-gateway` + container env; `tests/golden_prompts.json` (10-prompt acceptance suite incl. junk + injection), 5 requirement fixtures (1BHK–clinic; clinic uses `study` as consultation stand-in — closed-enum limitation, documented), `fixtures/lmstudio_smoke.sh`; 20 new tests.
- [x] **Step 0.2 — host LM Studio gate:** LM Studio CLI 1.3.3 and `qwen/qwen3.5-9b` Q4_K_M were present; the server was started on port 1234 bound to `0.0.0.0`, and the model loaded with full GPU offload, context 4096, parallel 1, and no TTL. Runtime verification: RTX 4060 GPU memory 7,253/8,188 MiB in use; native no-reasoning probe 54.43 tok/s, 0.52s time-to-first-token, zero reasoning tokens.
- [x] **Phase 1 — subdivision engine v0 + hard validator** (`mvp/phase1-engine`): `services/layout_engine/` — `geometry.py` (1 mm-epsilon Rect: overlaps/contains/shared_edge, corner contact ≠ adjacency), `subdivision.py` (balanced area-weighted guillotine: order-preserving halving, longer-side cuts, min-area clamped, facing-anchored so entry pulls to the facing edge; zero gaps/overlaps by construction), `engine.py` (expand+auto-entry → public/private facing bands → subdivide → leaf min-size gate → **deduplicated walls** (one per shared edge + boundary) → doors: `must`-adjacency first, then a BFS spanning tree from the circulation room so the access graph is connected by construction, narrow-door fallback, front door on the entry's facing wall; structured `DoesNotFitError` for undersized plots). `services/quality/hard_constraints.py` — pure fast validator: overlap / out_of_bounds / below_min_size / door-graph reachability. `services/export/render.py::layout_to_svg` + `scripts/render_debug.py` (all 5 fixtures render; 3BHK: 11 rooms / 34 walls / 12 doors). **Go/no-go gate passed:** Hypothesis property suite (200 random specs, derandomized) — the engine either returns a plan with zero hard violations or refuses with DoesNotFit, never broken geometry; the gate immediately caught (and we fixed) independent x/w rounding drift creating phantom 1 mm overlaps — edges are now rounded, widths derived. v0 limitations: single storey (floors>1 flattens), rotation always 0. New dev dependency flagged: `hypothesis==6.112.0`. 29 new tests.
- [x] **Phase 2 — extraction implementation + offline gate** (`mvp/phase2-extraction`): `services/llm_client.py::chat_structured` uses LM Studio's strict JSON-schema response mode, discovers the exact loaded model through `/v1/models`, disables Qwen reasoning for low-latency schema filling, caps output, serializes inference behind one process-wide GPU semaphore, and maps timeouts/connections/malformed output to typed failures. `services/extraction.py` adds the closed-vocabulary system prompt, pure synonym/explicit-count/feet/BHK normalization, prompt-grounded plot/facing enforcement, junk/injection neutralization, explicit conflict markers, and exactly one schema-correction retry before `ExtractionFailed`. No new dependency. Offline tests cover request shape, model discovery, timeout/unavailable/invalid output, concurrent serialization, normalization, prompt safety, and retry/failure behavior.
- [x] **Phase 2 live model acceptance gate:** `RUN_LLM_TESTS=1 pytest app/tests/test_mvp_llm_live.py -m llm -s -q` passed against the real local Qwen model. Structured-output smoke passed; golden extraction scored **10/10 on each of three consecutive runs** (required ≥8/10). The first probe exposed reasoning-only latency beyond 30s; `reasoning_effort: "none"` fixed it without raising the timeout. Default full backend regression: **624 passed, 2 live tests skipped, 1 existing dependency warning**.
- [x] **Phase 3 — deterministic clarification + transparent defaults** (`mvp/phase3-clarification`): `services/clarification.py::assess` routes validated requirements without model confidence — an empty program is `vague`, extraction conflict markers and structured `DoesNotFitError` are `conflict`, and complete-enough programs `generate` while surfacing plot/facing/bathroom questions as optional. `apply_defaults` remains the requested `RequirementsSpec → RequirementsSpec` bridge; `apply_defaults_with_report` additionally returns plain-language assumptions without mutating the source (9×12 m plot, east facing, and `max(1, bedrooms−1)` bathrooms). No schema or dependency change. The offline ten-prompt gate and the real Qwen extraction→clarification gate both route **10/10 correctly**. Fresh full regression command `python -m pytest app/tests -q`: **632 passed, 3 opt-in live tests skipped, 1 existing Starlette dependency warning**.
- [x] **Phase 3 known contract boundary:** the locked MVP schema has no per-room floor-preference field, so a contradictory “upstairs” instruction can only block when extraction preserves it as a `conflict:` marker; normal valid duplex phrasing is normalized to two floors. Plot-fit conflicts are fully structured through `DoesNotFitError` for Phase 4 API wiring.
- [x] **Phase 4 — authenticated API + existing-DB integration** (`mvp/phase4-api-db`): exact additive routes `POST /api/extract`, `/api/generate`, `/api/validate`, `POST /api/projects/{id}/versions`, and `GET /api/versions/{id}` orchestrate Phase 1–3 services behind existing short-lived access-token auth, rate limiting, generation entitlements, standard error envelopes, and workspace/project read/edit checks. Extraction returns a deterministic understood-summary and clarification decision; local-model failures map to a non-leaking 503; generation returns canonical requirements/layout/hard-quality plus transparent defaults; version saves always recompute quality server-side. Authorization is checked before quota charging or layout work.
- [x] **Phase 4 — backward-compatible persistence:** migration `015` adds nullable `requirements_json`, `canonical_layout_json`, and `quality_json` to the existing `DesignVersion` model. `layout_json` deliberately remains the established center-based canvas snapshot; `services/layout_adapter.py` deterministically maps canonical rooms/walls/hosted doors to existing canvas objects, so latest-design, versions, sharing, and the Sprint 19 editor remain usable. Project duplication carries canonical artifacts when present. Migration was verified PostgreSQL-reversible (`015 → 014 → 015`) and adds no dependency.
- [x] **Phase 4 live gate + regression:** `scripts/e2e_demo.py` (with Unix `e2e_demo.sh` wrapper) ran against real access-token auth, PostgreSQL, LM Studio, and Qwen: demo prompt → extract → generate → persist → fetch passed with 8 rooms and zero hard violations. That gate exposed an area-only subdivision bug (a bathroom became a 1.2 m sliver on a viable 30×40 ft plot); cut clamping now includes each descendant's shortest legal side, with a permanent demo-prompt regression test. Fresh command `python -m pytest app/tests -q`: **643 passed, 3 opt-in live tests skipped, 1 unchanged Starlette warning**.
- [x] **Phase 4 close-out:** defaults now raise a typed `ClarificationRequiredError` instead of bypassing a missing room program or unresolved conflict. Final verification: `python -m pytest app/tests -q` → **644 passed, 3 opt-in live tests skipped, 1 unchanged Starlette warning**; Alembic head and connected PostgreSQL are both `015`; 63 FastAPI method/path registrations contain no duplicates.
- [x] **Phase 5 — reviewed prompt-to-layout flow** (`mvp/phase5-2d-svg-editor`): the Project workspace calls the additive MVP `/api/extract` contract first, shows the deterministic understood summary, collects blocking clarifications, exposes optional assumptions, and then calls canonical generation. Engine selection remains safety-first: canonical single-floor requirements use the new deterministic engine; unsupported/multi-floor programs retain the established generator. The canonical adapter feeds the existing canvas store without replacing saved-layout compatibility.
- [x] **Phase 5 — shared-state editable SVG plan:** `Plan2D` renders every component-registry type (rooms, walls, openings, stairs, circulation, service, furniture, structure, and generic fallback) from the same Zustand state as 3D. It supports first-click selection, Inspector synchronization, thresholded footprint-clamped movement, eight anchored resize handles, click-to-place, tape measurement, fit/zoom, and right-drag navigation. The selected SVG object is painted last so walls/openings cannot intercept its resize handles.
- [x] **Phase 5 — interaction and persistence integrity:** SVG and WebGL modes share copy/paste, duplicate, delete, undo/redo, and Escape cancellation while editable fields remain protected. Resize paths enforce component minimums plus floor-footprint maximums, and move/resize gestures emit one final history/activity entry. Existing canvas serialization, drafts, named versions, share payloads, and component normalization remain unchanged. Until Phase 8 replaces export rendering, Plan mode retains a hidden read-only WebGL canvas solely for the existing thumbnail/PNG/PDF capture path.
- [x] **Phase 5 verification:** focused SVG/geometry/store/Project checks passed before the full gate; final `npm test` result is **185 passed across 29 files, 0 failed, 0 skipped**. `npx tsc --noEmit` passed and `npm run build` passed (1,132 modules). Full backend regression `..\.venv311\Scripts\python.exe -m pytest app/tests -q` passed with **646 passed, 3 expected live-model skips, 1 unchanged Starlette warning**. Live authenticated browser acceptance covered normal-language house extraction/review/defaults/generation, Plan rendering, selection, Inspector sync, drag, resize, interruption recovery, click-to-place, and zoom with no application console errors. Right-button pan is pinned by the automated pointer test because the browser controller cannot issue a right-button drag path.
- [x] **Phase 6 — canonical weighted quality + opt-in Vastu** (`mvp/phase6-quality-vastu`): `services/quality/scorer.py` keeps hard overlap/bounds/minimum/reachability failures separate and caps invalid layouts below the valid score range, then weights explainable adjacency, privacy, natural-light proxy, and bathroom/kitchen-separation rules. `services/quality/vastu.py` loads auditable compass-sector guidance from `vastu_rules.json` only when the prompt explicitly requests Vastu; ordinary prompts receive no Vastu deductions or warnings. The rules remain advisory conceptual-design checks, not code, construction, or professional-compliance certification.
- [x] **Phase 6 — API, persistence, and backward compatibility:** generation and canonical version saves persist the complete quality report beside requirements and layout artifacts; old hard-only snapshots still load. Fast `POST /api/validate` continues to validate the exact supplied geometry, while `?full=true` requires requirements and returns the weighted report. Full scoring and canonical saves deterministically rebuild deduplicated walls and hosted doors from edited room rectangles first, eliminating stale-opening reachability errors without relaxing strict initial generation. No migration or new dependency was added.
- [x] **Phase 6 — editor feedback and live refresh:** the shared right sidebar presents a compact Concept quality card in 2D and 3D, separates generic layout guidance from Vastu guidance, and labels hard-invalid states instead of displaying a misleading score. Canonical single-floor MVP room edits trigger one 300 ms debounced full validation; stale responses are discarded, report-only updates do not create history or dirty entries, and Vastu intent survives save/reload. Program Check remains the higher-priority source when structured Sprint 23 checks are available.
- [x] **Phase 6 verification:** final backend command `..\.venv311\Scripts\python.exe -m pytest app/tests -ra` collected 705 tests and completed with **702 passed, 0 failed, 3 expected live-LM skips, 1 unchanged Starlette warning**. Final frontend command `npm test -- --run --maxWorkers=1 --minWorkers=1` completed with **254 passed across 50 files**; `npx tsc --noEmit` and `npm run build` passed (1,165 modules). Authenticated browser QA on a persisted 2BHK verified 91/100 generated quality, an accurate minimum-size failure after resizing Bedroom 1, no stale all-room reachability cascade, and restoration to 91/100 through Undo; no application console errors were observed.
- [x] **Phase 6 known limits:** live canonical re-scoring is intentionally restricted to single-floor MVP layouts; legacy and multi-floor layouts retain their established validation paths. Rebuilt walls/doors are used by server scoring and canonical saves, but the editor does not yet repaint those derived visual objects immediately after each room edit. Vastu remains an opt-in directional preference layer, and the daylight check is an exterior-edge proxy rather than solar analysis.
- [x] **Phase 7 — live derived-geometry synchronization and shared invalid feedback** (`mvp/phase7-two-way-sync`): additive `POST /api/validate?full=true&includeLayout=true` responses can return the server-rebuilt canonical layout alongside quality. Canonical single-floor room edits replace only derived wall/door canvas objects, so visual openings, reachability scoring, and saved geometry use the same room rectangles without disturbing user-authored components. Hard-violation room ids now produce coordinated invalid styling in both SVG Plan and 3D Edit views.
- [x] **Phase 7 — quarter-turn editing and persistence integrity:** room rotation is canonicalized to 0/90/180/270 degrees; the Inspector exposes only those valid Y rotations, and the adapter converts between local box dimensions and visible world bounds so 90/270-degree rooms keep the same footprint through validation, save, reload, and version restore. Existing non-room object compatibility remains unchanged.
- [x] **Phase 7 — intentional 3D resize and history correctness:** selected rooms expose four restrained corner grips in 3D. Dragging keeps the opposite corner anchored, respects snap/minimum dimensions/footprint bounds and quarter-turn axes, disables camera controls only for the active gesture, and safely ends on release, cancel, Escape, blur, or pointer-capture loss with one final `object.resized` history entry. Undo/Redo snapshots now restore matching validation metadata as well as geometry, preventing stale warnings or invalid highlights after history navigation.
- [x] **Phase 7 persistence and regression coverage:** focused tests cover canonical rotated-room world-bound round trips, canvas serialize/reload, save/draft integrity, project loading, actual version-Restore fetch/load behavior, 3D resize geometry, validation refresh, and Undo/Redo controls. No migration or runtime dependency was added, and the legacy/multi-floor editor paths remain available.
- [x] **Phase 7 verification:** backend command `..\.venv311\Scripts\python.exe -m pytest app/tests -ra` collected 707 tests and completed with **704 passed, 0 failed, 3 expected live-LM skips, and 1 unchanged Starlette warning**. Frontend command `npm test -- --reporter=json --outputFile=C:\tmp\archiai-phase7-vitest.json --maxWorkers=1 --minWorkers=1 --no-file-parallelism` completed with **271 passed across 54 files, 0 failed, 0 skipped**; `npx tsc --noEmit` and `npm run build` passed (1,167 modules). `docker compose ps` reported PostgreSQL, backend, and frontend healthy; `/api/health` reported DB `ok` and the intentionally stopped LM Studio service `unreachable`, while the frontend returned HTTP 200.
- [x] **Phase 7 browser evidence and known limits:** authenticated browser QA verified 90-degree Inspector rotation, matching validation against the visible footprint, synchronized 2D/3D selection and quality feedback, and no application console errors. After the frontend container rebuild, the browser controller's local-URL security policy blocked the final direct grip-drag replay; a five-minute manual 3D resize check remains required before merge. Live derived synchronization remains intentionally limited to canonical single-floor MVP room geometry; rooms remain rectangular and axis-aligned at quarter turns; 3D grips are room-only; the existing Vite CJS/module warnings, React test `act` warnings, and large-bundle warning are unchanged.
- [ ] **Review gate:** stop here for owner acceptance after Phase 7. Phase 8 server-side PNG/PDF, pinned share links, DXF/IFC, and Phase 9 hardening remain intentionally unstarted.

### Sprint 23 - Structured Program Check and Constraint Integrity (first vertical slice)

- [x] **Parser integrity:** explicit building-type language now wins over generic BHK inference; numeric attached-ensuite phrasing and coordinated adjacency phrases (for example, "kitchen next to dining and utility") preserve every requested relation.
- [x] **Structured program contract:** generation metadata now records normalized requested spaces, counts, area/dimension ranges, zones, floor/daylight/privacy/exterior requirements, instance ids, site facts, and typed constraints without changing the legacy room/layout JSON contract.
- [x] **Explainable validation:** ProgramGraph scoring evaluates MUST, SHOULD, AVOID/separation, daylight/exterior, and orientation checks with `satisfied`, `warning`, `failed`, `missing_dependency`, or `not_evaluated` status plus human-readable evidence. The same metadata is returned by the API and persisted in DesignVersion snapshots.
- [x] **Constraint-aware graph packing:** a bounded deterministic row-repair pass preserves exact shared-wall MUST pairs and forbidden adjacencies when geometry permits. Existing tile/BSP/graph candidate safety remains intact; no random search, new engine, or fallback removal was introduced.
- [x] **Shared Program Check UI:** 2D Plan, 3D Edit, Zoning, Room Graph, and selected-object properties all consume one typed validation model. Selecting a room filters the check list to constraints relevant to that room; older saved layouts retain the existing local-check fallback.
- [x] **Normal-user anchor gate:** the 14-space east-facing house brief selected the graph engine at score 61, generated 14/14 requested spaces with no missing/extra rooms, passed 24 checks, failed 0, and surfaced 2 honest soft warnings (foyer/living adjacency and one bedroom daylight condition).
- [x] **Verification:** `..\.venv311\Scripts\python.exe -m pytest -ra` -> **680 passed, 3 expected live-model skips, 1 unchanged Starlette warning**; `npm test` -> **244 passed across 46 files**; `npx tsc --noEmit` and `npm run build` passed. Authenticated browser QA confirmed persisted summary counts and all four Kitchen-scoped checks as satisfied; no application console errors were observed.
- [ ] **Review gate:** stop after this vertical slice. Geometry collision/highlight work, richer editor feedback, openings/circulation, dashboard/telemetry, broader prompt expansion, and the remaining master brief stay deliberately deferred until owner acceptance.

### Sprint 24 - 2D Plan Editor Visual Parity (reference-driven slice)

- [x] **Unified architectural editor shell:** the 2D workspace now uses one dark graphite visual system across the top bar, centered view tabs, labeled left tool rail, right details panel, prompt command bar, and bottom status strip. The separate floating 2D program panel is removed; program and validation information live in the sidebar.
- [x] **Plan drawing hierarchy:** room fills are muted and legible, unselected rooms show quiet names, selected rooms add inline dimensions, and purple selection/resize handles replace the former oversized high-contrast treatment. Overall footprint dimensions, a north compass, facing/road context, and main-entry annotation render around the plan.
- [x] **Selection and geometry panel:** selecting a room keeps the plan readable while exposing width, depth, area, and perimeter in a compact sidebar card. Less-common type, floor, position, height, and rotation controls remain available under Advanced properties; duplicate and delete remain explicit.
- [x] **Program Check parity:** the sidebar shows requested/generated counts, satisfied/warning/failed totals, explainable checks, current-floor metrics, and a building-program summary from the same typed validation state used by the other editor views.
- [x] **Collision-free controls:** the drawing surface reserves header/footer space, the tape panel appears only in intentional measure mode below the header, and zoom controls sit outside the command bar. Live browser QA at 1280x720 drove these placement fixes.
- [x] **Backward compatibility:** generation, refine, 3D, zoning, room graph, Zustand layout state, serialization, autosave, versions, export/share capture, and existing component interactions are unchanged. No backend schema, API, dependency, or layout-engine change is part of this slice.
- [x] **Verification:** `npm test -- --run` -> **244 passed across 46 files**; `npm run build` passed (1,162 modules); TypeScript passed as part of the production build. Authenticated live browser QA covered room selection, selected-room geometry, measure-mode placement, 2D -> 3D -> 2D switching, and console inspection with zero application errors.
- [ ] **Review gate:** stop here for owner visual acceptance before expanding editor behavior or starting another product phase.

### Packet 7.1 — Program Truth Gate (post-Phase-7 quality gate, prerequisite to `archiai_engine_generalization_workflow.md`)

> Inserted between the Phase 7 review gate and the engine-generalization workflow per the owner's plan: fix the live-tested extraction defect and close the "quality can call a broken layout satisfactory" gap before any engine-generalization work (Packets 7.2+) starts.

- [x] **Root-cause fix — hyphenated count extraction:** `services/extraction.py::_explicit_count` required whitespace between a count token and its noun (`\s+`), so a live-tested brief ("...compact single-floor **2-bedroom** house on a 12m x 15m east-facing plot...") extracted only 1 bedroom instead of 2 — the hyphenated adjective form silently bypassed the deterministic count-correction safety net while "2 bedrooms"/"two bedrooms"/BHK forms already worked correctly. Separator widened to `[\s-]+`; a regression test pins the exact failed prompt.
- [x] **Prompt-to-program truth gate — missing-requested-room hard violation:** `services/quality/hard_constraints.py::validate` gains an optional `requirements: RequirementsSpec | None = None` parameter; when supplied, a requested space type/count short in the generated `LayoutPlan` is now a hard violation (`missing_requested_room`), capping the score below the valid range instead of silently scoring "satisfactory." Optional and backward-compatible: the fast per-drop `/api/validate` editor-sync path and all existing `validate(plan)` call sites are unaffected; only `quality/scorer.py::score` (which already has both plan and requirements) passes it through.
- [x] **Tests:** `test_mvp_extraction.py` — new hyphenated-count regression test (15/15 passing in that file, including the pre-existing "two-storey"/BHK/number-word cases). `test_mvp_quality.py` — new hard-violation test (a missing bedroom caps the score ≤ 49) plus a backward-compatibility test (`validate(plan)` / `validate(plan, None)` stay geometry-only, unaffected by the new parameter).
- [x] **Verification:** full backend `pytest app/tests -ra` — **707 passed, 3 expected live-LM skips, 0 failed** (baseline plus the 3 new tests). Frontend `npm test -- --run` — **271 passed across 54 files, 0 failed** (untouched; confirms no incidental regression). Live end-to-end check against the running LM Studio server (`qwen/qwen3.5-9b`) with the exact originally-failing prompt: extracted **2 bedrooms, 2 bathrooms**, plot 12×15 m, east-facing — all correct.
- [x] Commit `4c9ad6f` on `mvp/phase7-two-way-sync` (not merged, not pushed).
- [ ] **Deferred:** Packets 7.2–7.9 (engine benchmark/gtree audit, canonical `ProgramGraph` promotion, deterministic layout archetypes, real circulation, bounded candidate search, generalized `SpaceCatalog`, rule packs, true multi-floor) per `archiai_engine_generalization_workflow.md` — none started. This packet only closes the specific live-tested extraction defect and adds the completeness safety net; it does not change the engine's residential-only vocabulary, single-candidate generation, or house-only band-split placement.
- [ ] **Review gate:** stop here for owner acceptance before starting Packet 7.2.

### Phase 7 close-out — editor UI fixes and the manual 3D resize QA

> Closes the one item the Phase 7 entries above left open: "a five-minute manual 3D resize check remains required before merge." Also folds in four editor UI fixes reported directly against the running app during this pass.

- [x] **3D context card shown in the wrong view:** `ThreeDContextCard` (isometric preview + "Open in 3D" shortcut) was gated `viewMode === '3d'`, so it only appeared once already inside 3D Edit — the one view where a preview-of-3D is redundant clutter. Flipped to show in every view except 3D Edit. Commit `b4fcb9e`.
- [x] **Tool rail had two different looks across views:** `ToolRail`'s `labeled` flag was `viewMode === 'floor_plan'`, giving 2D Plan a labeled bordered panel and 3D Edit/Zoning/Room Graph an unlabeled icon-only rail with hover tooltips — same tools, different UI per view. Unified on the labeled panel everywhere. Commit `a15d964`.
- [x] **Dimension labels overlapped into unreadable text on a selected room:** the plain name label showed area underneath, and `DimensionAnnotations`' own area+dims badge rendered only 0.3 world-units above it — two overlapping area readouts crowding into garbled text at normal zoom (reported directly: a selected "Bedroom" showing overlapping "7.7 / 4.6 / 7.7 / 35.1" text). Suppressed the name label's area line when selected (the dedicated badge already covers it) and widened the gap to 0.95 units. Commit `be64b77`.
- [x] **Space Program panel left a large empty gap in 3D Edit after the context-card fix:** `ProgramPanel`'s `top-[15.5rem]` override existed only to clear the (now-hidden) context card; removed so it falls back to the component's own default position right below the top bar. Commit `6abf93f`.
- [x] **Verification for all four UI fixes:** `npx tsc --noEmit` clean, `npm test -- --run` **271 passed / 54 files, 0 failed** (each time), `npm run build` clean (only the pre-existing bundle-size warning). Confirmed visually together in the browser against the `trial` project: no context card in 3D Edit, consistent labeled rail in all four views, Space Program flush under the top bar, clean non-overlapping labels on a selected room.
- [x] **Manual 3D resize-grip QA performed** (the item Phase 7 left open): using the `trial` project's saved layout, confirmed via direct DOM/geometry reads (not just visual inspection) rather than pixel-guessing alone —
  - **Resize mechanics:** dragged 3 of the 4 corner handles to a genuine resize (not a move) across two different rooms — Living Room's NW and SE corners (both axes change together, anchored correctly at the opposite corner) and Bathroom 1's corner nearest the plot edge (correctly clamped to a footprint boundary on one axis while the other resized freely, identical clamping behavior seen on both rooms). The 4th corner could not be reliably isolated from neighboring rooms' hit-areas in this remote-browser session, so it was not independently confirmed by drag alone — however all 4 handles share one function (`CORNER_RESIZE_HANDLES` + `resizeRoomFromWorldCorner`) differing only by a sign constant already covered by `resizeHandleGeometry.test.ts`, and 3 of the 4 sign combinations were now confirmed end-to-end through the real pointer-event/store/UI wiring.
  - **Undo/Redo:** Undo restored exact pre-resize values (bit-for-bit) across 6+ separate resize/move attempts in this session. Redo re-applied a resize with bit-for-bit identical values to the original resize.
  - **Save/reload:** saved a resized room, reloaded the project from scratch (fresh network fetch, new store), and the resized geometry matched the pre-reload values to full floating-point precision (`Width 8.715051096695742`, `Depth 7.5`, etc., unchanged through the JSON round-trip). Named-version-restore (a separate history-drawer flow) was not separately exercised, but it reads through the identical persisted-layout path just proven.
  - **Incidental finding, not a defect:** an aggressive test resize made Living Room overlap four neighbors; the quality panel correctly flagged each overlap by name and marked the layout invalid rather than silently accepting it — confirms the overlap hard-check still fires correctly from live UI edits, not just fixtures.
  - **Incidental confirmation of Packet 7.1:** this same `trial` project's saved requirements ask for 2 bedrooms, but its saved layout only has 1 — a pre-existing artifact predating the Packet 7.1 fix. The `missing_requested_room` hard violation added in Packet 7.1 correctly flagged it live ("Requested 2 bedroom(s) but the layout only has 1") the moment a validation pass ran, exactly as designed. Not fixed here (out of scope — it's the demo project's stored data, not code), left as-is.
  - Cleanup: the test resize was reverted (Properties-panel fields set back to the exact original values) and re-saved, so `trial` is back to its original 180 m², non-overlapping state.
- [x] Backend full suite re-verified after this pass: `pytest app/tests -ra` — **707 passed, 3 expected live-LM skips, 0 failed**. Frontend: **271 passed / 54 files, 0 failed**.
- [x] **Review gate: CLOSED.** Phase 7 is complete — code and the manual resize QA it was waiting on. Not merged into `main`, not pushed beyond `origin/mvp/phase7-two-way-sync` unless separately requested. Next up per the owner's plan: Packet 7.2 (Engine Benchmark and Gtree Audit).

### Packet 7.2 — Engine Benchmark and AVOID-adjacency root-cause finding (`packet7.2/engine-benchmark-audit`)

> Branched off fresh `main` after PR #34 merged. Scope: establish a real, measured baseline across the acceptance prompt matrix (per `archiai_engine_generalization_workflow.md`) before any engine-generalization work starts, and investigate the highest-signal issue the baseline surfaces. Full writeup, including the reverted fix attempt and why, lives in `archiai_engine_generalization_workflow.md` §0.4 — this entry is the summary.

- [x] **Real baseline, not an estimate:** `backend/scripts/benchmark_acceptance_prompts.py` runs all 6 acceptance prompts through the actual `parse_prompt → generate_layout` production path and scores each with the existing `layout_quality_service`. Results saved in `backend/scripts/benchmark_baseline_before_avoid_fix.md`: quality scores 51–87, generation confirmed deterministic (once compared on geometry rather than the fresh UUID each `id` field gets — the naive full-dict comparison falsely reported non-determinism until fixed), and **AVOID-adjacency violations in 5 of 6 prompts** (Kitchen next to Bedroom/Bathroom recurring across house, two-floor-house, accessible-home, office, restaurant).
- [x] **Root cause traced precisely:** `_order_zone_rooms`/`_chain_by_adjacency` — the room-ordering logic every tiled candidate goes through — accept `must_pairs`/`should_pairs` only. There is no `forbidden_pairs` parameter anywhere in placement; AVOID constraints are only ever a post-placement score penalty, so no candidate `generate_layout` produces can actually structurally avoid a bad adjacency.
- [x] **A fix was attempted, tested, and reverted — correctly, not abandoned early:** extended the existing MUST-pair cross-row repair (in `_graph_pack_rooms`) to also relocate an AVOID-paired room. Live benchmark showed **zero change**. Diagnosed why: when the conflicting type has multiple instances (two bedrooms), relocating one instance leaves the other still adjacent, so the type-level violation count — and the tie-break that would select the repaired variant — never changes. Also surfaced that `_graph_pack_rooms` only activates when `must_pairs` is non-empty, so it never even ran for these AVOID-only benchmark cases — the first fix attempt targeted the wrong one of the three placement paths (`_tile_rooms`, `_bsp_partition_rect`, `_graph_pack_rooms`) `layout_service.py` currently maintains. Reverted cleanly (`git diff` on `layout_service.py` is empty) rather than leave ineffective code in the core engine.
- [x] **Confirms, with evidence, why Phase 4/5 of the generalization workflow exist:** this is not fixable with a bounded per-room repair; it needs either zone/row-boundary awareness (Phase 4 circulation) or real multi-candidate search that can generate and prefer a structurally-separated layout (Phase 5). Documented in the workplan doc precisely so a future attempt starts from this diagnosis instead of re-discovering it.
- [x] Full backend suite unchanged after this packet: **707 passed, 3 expected live-LM skips, 0 failed** — no engine code changed, only new benchmark tooling added.
- [ ] **Not done in this packet (by design — Packet 7.2 was audit-only):** no code fix for the AVOID-adjacency gap; that's Packet 7.3+ once the ProgramGraph/archetype work (or a scoped zone-boundary fix) is designed properly, not patched under time pressure.

### Phase 1 — SpaceCatalog (`phase1/space-catalog`, off `main` after Packet 7.2)

> First real step of `archiai_engine_generalization_workflow.md`'s Phase 1-9 plan (Phase 0 was Packet 7.2's audit). Branched fresh since Phase 1 has no dependency on Packet 7.2's benchmark tooling beyond the diagnostic value.

- [x] **Audit first, per the doc's own Step 1.1:** `backend/scripts/audit_catalog.py` diffs `ROOM_SIZING` (12 residential types, real min dimensions) against `BASE_SIZES` (37 free-string types, area only). Real result (`backend/scripts/catalog_audit_output.md`): **11 of 12 overlapping types conflict on area** — only `bedroom` already agreed (12.0 m² both). Confirms the doc's own worked example (bathroom: 4.0 vs 6.0) and shows the disagreement is the norm, not the exception.
- [x] **`app/services/catalog/space_catalog.py`:** a single free-string-keyed `SpaceType` registry (37 entries) resolving every conflict the audit found with one documented rule: `BASE_SIZES` wins for `preferred_area_m2`, `ROOM_SIZING` wins for `min_w`/`min_d` where both exist (bathroom keeps its real 1.5×2.1 m minimum, not something invented). A type with no `ROOM_SIZING` minimum gets one derived from area (near-square, 60% of preferred, floored at 1.2 m) rather than left undefined. `get()`/`resolve_alias()` never guess — an unmatched key raises `UnknownSpaceType` with a `difflib`-based suggestion (`"bedrom"` → suggests `"bedroom"`); `register()` is the escape hatch for a type nobody templated (e.g. `"recording_studio"`).
- [x] **Purely additive:** no existing module imports this package yet, and it imports nothing that would create a cycle — zero behavior change to anything already running. `zone`/`node_type`/`wet_room`/`needs_exterior`/`privacy_level` classification is a fresh copy of the values already living in `planning/program_graph.py`/`program_validation.py` (not a cross-import of their private names), since this module is meant to *become* the one home for that classification once Phase 1.2 wires the delegation — that wiring is deliberately not part of this slice.
- [x] **Tests:** `test_space_catalog.py` (28 tests) — every one of the 12 legacy `RoomType` enum values round-trips through `get()`; the bathroom conflict resolves exactly as documented; enum-only names (`dining`/`entry`/`utility`/`parking`) alias to their free-string form (`dining_room`/`foyer`/`laundry`/`garage`); all 5 existing requirement fixtures (`1bhk`–`4bhk`, `clinic`) resolve their room types untouched.
- [x] **Verification:** full backend suite **735 passed** (707 baseline + 28 new), 3 expected live-LM skips, 0 failed — confirms the "purely additive" claim, not just asserts it.
- [ ] **Not done in this slice (next slices, per the doc's own Phase 1.2):** `schemas/requirements.py` doesn't consume the catalog yet (`RoomType` enum is unchanged); `layout_engine/engine.py`/`quality/*` don't read from it yet; the frontend contract (`contracts.ts`, room color mapping) is untouched. Phase 1 is a 4-5 day estimate in the doc; this is its first, safely-scoped sub-step, not the whole phase.

**Phase 1.2 — SpaceRequest/spaces on the contract (migration order item 1):**

- [x] `SpaceRequest` (`space_type: str`, `count`, `size_hint`, `area_m2`) added to `schemas/requirements.py`; `RequirementsSpec.spaces: list[SpaceRequest]` added alongside the existing `rooms` field, defaulting to `[]`. Nothing existing reads `spaces` yet — `rooms`/`RoomRequest`/`RoomType` are completely unchanged.
- [x] `spaces_from_rooms()` (`app.services.catalog`) maps legacy rooms to catalog-keyed spaces losslessly — proven for **every** `RoomType` enum value and all 5 existing fixtures, not a sample.
- [x] **Caught and fixed a real ripple effect, not a false pass:** adding the new field with its default made 3 `test_mvp_api.py` assertions fail — they compared a persisted/serialized `RequirementsSpec` against the *raw pre-migration fixture dict* by exact equality, and the persisted model now legitimately carries one more key (`spaces: []`). Fixed by updating the expected value to `{**spec, "spaces": []}`, not by reverting the schema change. Searched the whole suite for every other `== spec`-shaped comparison first and confirmed the other two (`test_mvp_clarification.py`, `test_mvp_contracts.py`) compare model-to-model — both sides already carry `spaces=[]` consistently, so they needed no fix.
- [x] **Verification:** full backend suite **747 passed** (735 + 12 new), 3 expected live-LM skips, 0 failed. One run showed 13 scraper-test failures (`test_scraper_fetcher.py`/`test_scraper_pipeline.py`) that did not reproduce on an immediate rerun with zero code changes between attempts — investigated, confirmed transient/environmental (unrelated code path, no import or behavior touched by this change), not a real regression.
- [ ] Still not done: nothing yet *consumes* `spaces` for generation or quality scoring — that's later Phase 1.2 items (porting the engine/quality to read `spaces`) and Phase 2 (ProgramGraph as canonical input).

### Phase 2.1 — `EngineProgram` bridge (`phase1/space-catalog`, stacked on Phase 1.2)

> First sub-step of the doc's Phase 2 ("Promote `ProgramGraph` to the canonical engine input"), split deliberately into two slices: 2.1 (this one) is a pure additive bridge — `layout_engine/engine.py` is untouched and still runs exactly as before. 2.2 (refactoring `engine.py` to actually consume `EngineProgram`, byte-identical output required) is separate, riskier follow-up work, not started.

- [x] **`EngineProgram` dataclass + `to_engine_program()`** added to `planning/program_graph.py` (exported from `app.services.planning`): `needs: list[RoomNeed]` (reuses the engine's own subdivision type, keyed by **node id**, not type), `zone_of`/`floor_of` dicts, `must_adjacent`/`should_adjacent`/`avoid` as **id-level** tuple lists, `circulation_nodes`, `entry_node`.
- [x] **Sizing precedence implemented as documented** ("explicit area > size_hint × multiplier > catalog default"): a node's own `target_area_sqm`/`min_width_m`/`min_depth_m` win when set; else a new `Node.size_hint` field (nothing produces it yet — added ahead of its producer, same accepted pattern as Phase 1.2's `SpaceRequest.size_hint`) scales the catalog default; else the catalog default; an unresolvable `space_type` falls back to `width × depth` rather than raising, since `to_engine_program` must stay usable on partially-specified graphs. Hard minima (`min_w`/`min_d`) never scale with `size_hint` — only the preferred/target area does.
- [x] **Edge bucketing is id-level, fixing the exact bug Packet 7.2 diagnosed:** two bedroom nodes each keep their own MUST/AVOID pairs instead of collapsing onto a `("bedroom","bathroom")` type pair (the root cause `_order_zone_rooms`/`_chain_by_adjacency` has in the legacy engine). `relation_type="separated"` or `strength="AVOID"` → `avoid`; `strength="MUST"`/`"SHOULD"` with an adjacency-shaped `relation_type` (`adjacent`/`connected_by_door`/`near`) → `must_adjacent`/`should_adjacent`.
- [x] **Tests:** `test_engine_program.py` (16 tests) — every sizing-precedence tier, id-level must/avoid bucketing (including the two-bedroom case), `zone_of`/`floor_of` coverage, `circulation_nodes`, `entry_node` resolution (and its `None` case), buildable-node filtering (openings/structural excluded).
- [x] **Verification — with an honest caveat:** could not run the full backend suite via `pytest` this session — `app/tests/conftest.py` unconditionally imports `app.main`, which imports the scraper router, which imports `scrapling`; import-time header generation in `scrapling`'s bundled `browserforge` dependency now raises (`chrome_version=148` hardcoded in the pinned scrapling commit has zero matches in the freshly-downloaded, current fingerprint dataset). Root-caused (confirmed via isolated repro, tried a `browserforge` downgrade, still fails) as a pre-existing dependency version-skew bug, **unrelated to this change** and blocking the *entire* suite's collection, not just these new tests. Verified instead by executing every assertion from `test_engine_program.py`, plus the existing golden `test_program_graph.py` round-trip/identical-layout checks and `test_space_catalog.py` spot-checks, directly against the real modules (no mocks) — all pass. `pytest`-based verification should be re-run once the `scrapling` pin is fixed.
- [ ] **Not done in this slice:** `layout_engine/engine.py` does not consume `EngineProgram` yet (Phase 2.2); no `from_requirements()` builder yet (also 2.2); `program_completion.py` (auto-entry-injection-as-a-graph-rule) is Phase 2.2/4.

### Phase 2.2a — `from_requirements()` adapter (`phase1/space-catalog`, stacked on 2.1)

> Still not wiring `engine.py`. The doc's 2.2 bullet list bundles three things (graph construction, deleting the auto-entry hack, `_order_group` reading id-level `must_adjacent`) into one refactor with a byte-identical-output acceptance bar — that refactor is real engine-behavior surgery and deserves its own careful slice. This one only builds the adapter it depends on.

- [x] **`from_requirements(spec) -> ProgramGraph`** added to `planning/program_graph.py` (exported from `app.services.planning`), parallel to the existing `from_parser_output`/`from_building_template`/`from_user_objects` adapters. Uses `spec.spaces` when the caller populated it, else normalizes `spec.rooms` through `catalog.spaces_from_rooms()` — matches every real caller today, which only sets `rooms`.
- [x] **`spec.adjacency`/`spec.avoid_adjacency` are still `RoomType`-keyed** (the closed enum hasn't left the contract), so each pref is resolved to its catalog key (`RoomType.entry` → `"foyer"`, etc.) before matching nodes by `space_type` — and every matching node pair gets its own edge, not one edge per type. Verified against the real `3bhk_adjacencies` fixture (2 bathrooms): `pooja_room~bathroom` AVOID produces 2 edges, one per bathroom instance, not 1.
- [x] **Deliberately does NOT auto-inject an entry node.** `engine._expand()`'s `counts[RoomType.entry] = 1` hack stays exactly where it is until Phase 2.2b actually replaces it with a `program_completion.py` graph rule — this adapter is a faithful structural translation only, not a preview of that rule.
- [x] **Tests:** 6 new cases in `test_engine_program.py` (22 total in the file now) — `spaces`-over-`rooms` precedence, no-auto-entry, enum-to-catalog-key alias resolution (clinic fixture's `entry~living_room` must edge lands on the `foyer` node), id-level avoid bucketing across both bathroom instances, and a full round-trip through `to_engine_program` on the `3bhk_adjacencies` fixture (8 needs, 4 avoid edges, 2 must edges — hand-verified against the fixture's own adjacency list).
- [x] **Verification:** same `pytest` blocker as Phase 2.1 (unrelated `scrapling`/`browserforge` import failure — see below, now flagged as its own task). Verified by executing every new assertion directly against the real modules, plus a full re-run of the Phase 2.1 checks and the golden `test_program_graph.py` suite (6 prompts × round-trip + identical-layout, template/user-object/merge/validate adapters) to confirm this addition caused no interference. All pass.
- [x] **Flagged, not fixed, as its own task:** the `scrapling`/`browserforge` pytest blocker is environment-wide, not specific to this change, and out of scope for an engine-generalization slice — spawned as a separate background-task suggestion (`Fix scrapling/browserforge blocking all backend tests`) with the full repro/diagnosis instead of silently living with it.
- [ ] **Not done in this slice (Phase 2.2b, next):** `engine.py` itself still calls `_expand(spec)` unchanged — `generate_plan()` behavior is 100% unmodified. Swapping it for `graph = from_requirements(spec); program = to_engine_program(graph)` plus the real auto-entry-as-graph-rule and `_order_group` reading `program.must_adjacent` is the acceptance-gated, byte-identical-output refactor that comes next.

### Phase 2.2b — `engine.py` actually consumes the graph pipeline (`phase1/space-catalog`, stacked on 2.2a)

> The real, riskier refactor: `layout_engine/engine.py`'s `_expand(spec)` (a flat dict-counting loop) is replaced by `ensure_entry(from_requirements(spec))` → `to_engine_program(graph).needs`. `generate_plan()`'s output must be byte-identical to before (ids aside) for all 5 requirement fixtures — verified against a real pre-refactor snapshot, not assumed.

- [x] **Two real design conflicts found and resolved before wiring anything in** (both would have silently changed generated geometry if missed):
  1. **Area/minima disagreement:** the Phase 1 catalog resolves `preferred_area_m2` from `BASE_SIZES`, which disagrees with `ROOM_SIZING` on 11 of 12 residential types (confirmed by direct query: bathroom 4.0 vs 6.0 m², kitchen 9.0 vs 14.0 m², etc.). `from_requirements`'s `spec.rooms` branch does **not** route through `catalog.spaces_from_rooms()` — it builds nodes directly from each `RoomRequest`, setting `target_area_sqm`/`min_width_m`/`min_depth_m` explicitly from `ROOM_SIZING[room.type]`, so `to_engine_program`'s "explicit wins" precedence keeps residential sizing untouched. The catalog only actually resolves sizing for the (currently unused) `spec.spaces` path.
  2. **Vocabulary mismatch:** `engine.py`'s own zoning split does `RoomType(need.type) in PUBLIC_ROOM_TYPES` (`generate_plan`, `mvp_defaults.PUBLIC_ROOM_TYPES`/`PRIVATE_ROOM_TYPES`) — this **requires** `RoomNeed.type` to be a real `RoomType` enum string, which raises `ValueError` for a catalog-aliased key like `"dining_room"`/`"foyer"`. `from_requirements`'s `spec.rooms` branch therefore uses the **raw** `RoomType.value` (`"dining"`, `"entry"`, `"utility"`, `"parking"`) as `node.space_type`, not the catalog key — confirmed by grepping every use site of `PUBLIC_ROOM_TYPES`/`PRIVATE_ROOM_TYPES` in the repo (only `engine.py:374-375`). `nodes_for()` (adjacency matching) tries the raw value first, falls back to the catalog-alias key — so the `spec.spaces` path (free-string, no `RoomType`) still resolves correctly when populated. Also revisited and fixed 2.2a's own `program_completion.ensure_entry`/tests, which had assumed the catalog-key spelling (`"foyer"`) before this was understood — `ensure_entry` now checks/injects `"entry"` (raw), matching what `from_requirements` actually emits for RoomType-sourced programs.
  - **Small, in-scope, zero-risk side fix:** `_PUBLIC_TYPES`/`_DAYLIGHT_TYPES`/`_OPEN_PLAN_TYPES`/`_SERVICE_TYPES` in `program_graph.py` were missing `"dining"`/`"parking"` as raw synonyms of `"dining_room"`/`"garage"` (the `"entry"`/`"foyer"` and `"utility"`/`"laundry"` pairs already existed) — a real, pre-existing classification gap only reachable via the new raw-value path (confirmed the parser already normalizes prompt text to the canonical spellings, so this never affected any other adapter). Added the two missing synonyms, mirroring the existing pattern.
- [x] **`planning/program_completion.py`** (new): `ensure_entry(graph)` replaces `engine.py`'s old inline `counts[RoomType.entry] = 1` hack. Idempotent, checks both `"entry"`/`"foyer"` spellings. Building-type-aware completion (reception for a clinic, lobby for an office) stays Phase 4 per the workflow doc — this is the seam, not the generalization.
- [x] **A real, subtle bug found and fixed via golden-diff testing, not assumed away:** captured `generate_plan()`'s exact output (rooms/walls/doors, geometry only) for all 5 fixtures *before* touching `engine.py`, then diffed after wiring. Rooms and walls matched byte-for-byte immediately, but doors did not for 2 of 5 fixtures — for `4bhk` specifically, door **count** differed (15 vs 14), not just order. Root cause: `_place_doors`'s BFS spanning tree (`generate_plan` → `_place_doors`) tie-breaks on `sorted(by_pair.items(), key=lambda kv: sorted(kv[0]))` — a **lexicographic sort of room key strings**. Switching the graph's own node-id scheme (`"node-3"`) in for the legacy `"r1".."rN"` scheme changes that sort order, which can change *which* doors a tied BFS pass picks — a real behavior change, not a cosmetic id difference, despite the doc's "byte-identical rooms, ids aside" phrasing suggesting ids don't matter. Fixed by remapping `to_engine_program(...).needs` keys back to `"r1".."rN"`, in the same list order the graph already produces (documented in `_expand`'s own docstring). Re-diffed after the fix: all 5 fixtures byte-identical, ids aside.
- [x] **A second, unrelated circular import surfaced and was fixed:** `layout_engine/__init__.py` eagerly imports `engine.py`; `engine.py` now imports `app.services.planning`; `planning/program_graph.py` imports `RoomNeed` from `layout_engine.subdivision`, which (being the first touch of the `layout_engine` package in some import orders) re-enters `layout_engine/__init__.py` mid-initialization, wanting `from_requirements`/`to_engine_program` before `program_graph.py` has finished defining them. Fixed by moving the `RoomNeed` import inside `to_engine_program()`'s function body (deferred to call time — safe since the module already has `from __future__ import annotations`, so the `EngineProgram.needs: list[RoomNeed]` field annotation never needed `RoomNeed` to be a real name at class-definition time). `add_requirements_node()` (renamed from a private helper so `program_completion.py` isn't reaching into another module's underscore-prefixed internals — the codebase's own established convention, e.g. `space_catalog.py`'s docstring on why it doesn't cross-import `program_graph.py`'s private frozensets) is the other new shared surface between `program_graph.py` and `program_completion.py`.
- [x] **Tests:** 4 new cases in `test_engine_program.py` (26 total) covering the raw-vs-catalog-key split and `ensure_entry`; 2 of 2.2a's existing tests fixed to match the corrected raw-value design (`test_must_adjacency_resolves_on_the_raw_entry_value`, `test_rooms_sourced_nodes_use_the_raw_room_type_value_not_the_catalog_key`); 1 new permanent regression test in `test_mvp_engine.py` (`test_room_ids_follow_the_legacy_r_n_scheme`, parametrized over all 5 fixtures) pinning the exact mechanism the door-count bug came from, since the file's existing invariant-only tests (by design, "never exact coordinates") would **not** have caught that regression — confirmed by checking which existing test would have failed and finding none would have.
- [x] **Verification (same `pytest` blocker, more surface covered than 2.1/2.2a):** captured and diffed the pre/post golden snapshot (above); re-ran every invariant test from `test_mvp_engine.py` directly against the real modules (valid-plan, fills-plot, determinism, entry-facing, attached-bathroom, wall-dedup, door-reachability, `DoesNotFitError` paths, `rebuild_derived_geometry` round-trip and disconnected-edit handling) — all pass; ran the project's actual 200-example derandomized Hypothesis go/no-go gate (`test_property_engine_output_never_violates_hard_constraints`'s exact strategy) directly — 200/200 pass, zero hard violations, zero failures; ran every test function in `test_engine_program.py` (26), `test_program_graph.py` (11), `test_space_catalog.py` (16), `test_mvp_contracts.py` (14) via direct module reflection — all pass. `test_mvp_api.py`/`test_mvp_clarification.py` need the async DB `client` fixture that only `conftest.py` (blocked) provides — confirmed they still *import* cleanly, but their actual assertions were not re-run this session; flagged as residual risk alongside the `scrapling` blocker itself, not silently assumed fine.
- [ ] **Not done in this slice (deliberately, with reasoning, not an oversight):** `_order_group` still reads `spec.adjacency` by **type**, not `program.must_adjacent` by **id** — the doc's own Phase 2.2 bullet list bundles this in, but doing so for `3bhk_adjacencies` (2 bathrooms, one `master_bedroom~bathroom` MUST) would try to pull *both* bathrooms adjacent to the master bedroom instead of just one, changing placement order and breaking byte-identical output for that exact fixture. Fixing the "only one bathroom of N gets attached" bug for real needs its own dedicated slice with its own acceptance test (does the *right* bathroom get attached, does the other still generate a valid plan) — not something to bundle silently into a "no behavior change" commit. `planning/program_validation.py`/graph-side quality scoring likewise still runs on the old `RoomSpec` bridge, untouched.

### Phase 3.1a — `zoned_bands`: catalog-driven banding replaces the residential-only split (`phase1/space-catalog`, stacked on 2.2b)

> First slice of workflow Phase 3 ("Generalize placement: layout archetypes instead of one residential recipe"). Scoped to just 3.1.a (`zoned_bands` generalization) + the minimal archetype registry/selector seam 3.2 asks for — `double_loaded_corridor`/`hub_and_spoke`/`open_core` and graph-shape-based selection among archetypes are unstarted, deliberately deferred until a second archetype exists to select between.

- [x] **The actual crash this fixes:** `generate_plan`'s zoning line was `RoomType(n.type) in PUBLIC_ROOM_TYPES` — this raises `ValueError` for any node whose `space_type` isn't one of the 12 residential enum values, so a `spec.spaces`-sourced (free-string, non-residential) program could never reach banding at all, regardless of what Phase 1's catalog or Phase 2's graph already supported upstream. New `layout_engine/archetypes.py::zoned_bands` bands off `EngineProgram.zone_of` (graph/catalog-derived) instead, so it no longer depends on the closed enum.
- [x] **`engine.py::_build_program`** replaces `_expand`: same graph-build-and-remap pipeline as Phase 2.2b's `_expand`, but now keeps and remaps the *whole* `EngineProgram` (`zone_of`/`must_adjacent`/`should_adjacent`/`avoid`/`circulation_nodes`/`floor_of`/`entry_node`) from the graph's `"node-3"` ids back to the legacy `"r1".."rN"` scheme, not just `needs` — Phase 2.2b deliberately discarded the rest since nothing consumed it yet; `zoned_bands` is the first consumer.
- [x] **Tried the literal 7-value `zone_of` as 7 top-level bands first, and reverted after it broke real fixtures on ordinary plot sizes.** A `public` band holding only kitchen+living (with entry/balcony/bathrooms peeled into their own separate bands) came out narrower than kitchen's own minimum width on a 9×12 m 2BHK — even though the *aggregate* of every band's floor comfortably fit the 9 m span. Root cause was two-fold, both documented in `archetypes.py`'s module docstring and `_band_floor`'s: (1) a naive greedy "peel one zone off at a time, clamp each to its own floor" allocation over-allocates early thin zones and starves later ones even when the aggregate fits — replaced with a "every band gets its floor first, then slack is distributed by preferred-area share" one-shot allocation; (2) the floor itself was area-only (`sum(min_area)/other`), missing the same per-room shortest-legal-side guard `subdivision._clamped_cut` already needed after the Phase 4 live-gate bug (a bathroom sliver on an otherwise-sufcient plot) — `_band_floor` now takes `max(area_floor, min_span_of_widest_room)`, mirroring `_clamped_cut` exactly.
- [x] **Settled on 3 macro-bands, matching the doc's literal "public → semi_private → private" wording**, not one band per `zone_of` value: circulation folds into public, service/technical/outdoor fold into private (`_MACRO_ZONE`) — real floor plans don't dedicate a whole facing-side band to just a foyer, or a same-size band to two bathrooms, and the finer split's starvation problem above confirmed that empirically, not just architecturally.
- [x] **Service redistribution:** a service-zoned room (e.g. bathroom) with a `must_adjacent` edge to a non-service partner moves into the *partner's* macro-band before grouping (`_redistribute_service`) — an ensuite attached to a public-zone room lands in the public band, not stranded in private by default.
- [x] **Must-adjacency ordering is now id-level, not type-level** (`_pull_must_adjacent`, reading `program.must_adjacent` id-pairs instead of the old `_order_group`'s `spec.adjacency` type-pairs). Confirmed this is safe against the exact case Phase 2.2b's own write-up flagged as risky (`3bhk_adjacencies`, 2 bathrooms, 1 `master_bedroom~bathroom` MUST): `from_requirements` already buckets that as MUST edges to *both* bathroom instances at the graph level, so id-level ordering now pulls both toward the master bedroom instead of the old code's "first bathroom by type only" — no test pins "exactly one bathroom attaches" (only "at least one," `test_attached_bathroom_touches_master_bedroom`), so this is a safe, incidental step toward the "only one bathroom of N gets attached" bug Phase 2.2b explicitly deferred, not a claimed fix of it.
- [x] **Old dead code removed, not left behind:** `_PUBLIC_ORDER`/`_PRIVATE_ORDER`/`_order_group`/`_bands` deleted from `engine.py`; `PUBLIC_ROOM_TYPES`/`PRIVATE_ROOM_TYPES` deleted from `mvp_defaults.py` after confirming (grep) `engine.py` was their only consumer (`prompt_service.py` has its own unrelated same-named frozensets for the legacy `layout_service.py` path).
- [x] **Tests:** new `test_archetypes.py` (9 tests) — single-zone passthrough, 3-band zero-gap/zero-overlap tiling summing to exact plot area, facing-side band is the public one, service-to-must-partner redistribution (with and without the must edge), id-level must-adjacency ordering, a synthetic **non-residential free-string program** (reception/consultation_room) banding without raising — the concrete proof this slice's stated goal works, `SubdivisionError` on an impossibly small plot, empty-program and `select_archetype` edge cases.
- [x] **Verification:** `pytest app/tests/test_mvp_engine.py` — all 30 invariants incl. the 200-example derandomized Hypothesis property gate and the id-scheme/attached-bathroom/determinism pins — green with zero changes to that test file. Full suite `pytest app/tests -q` — **788 passed, 3 expected live-LM skips, 0 failed** (779 baseline + 9 new `test_archetypes.py`). The `scrapling`/`browserforge` collection blocker flagged in Phase 2.1/2.2a's write-ups is resolved (commit `376db43`, already on this branch) — this was a normal, unblocked full-suite run, not a partial/manual one.
- [ ] **Known contract limit, not fixed here:** `PlanRoom.type` in `schemas/layout_plan.py` is still the closed `RoomType` enum (Phase 1.2's own deferred migration-order item 4, which explicitly touches the frontend contract — `contracts.ts`, room color mapping, `layout_adapter.py`). This means a `spec.spaces`-sourced non-residential program can now band correctly (proven above via `archetypes.py` unit tests bypassing `generate_plan`) but **`generate_plan()` itself still cannot serve one end-to-end** — it would still raise constructing the final `PlanRoom(type=RoomType(need.type))` for a free-string type like `"consultation_room"`. This slice fixes the banding half of the bottleneck; the `LayoutPlan` contract migration is real, separate, frontend-touching work, sized for its own gated packet.
- [ ] Everything else from workflow Phase 3 stays unstarted: `double_loaded_corridor`/`hub_and_spoke`/`open_core` archetypes, graph-shape-based `archetype_selector` (a real module wasn't created — YAGNI'd until there's a second archetype to select between), and retiring the legacy tiler as a fifth archetype.

### Phase 3.1b-d + 3.2 — three more archetypes + the graph-shape selector (`phase3/layout-archetypes`, off `phase1/space-catalog`)

> Completes the workflow doc's "P3 Archetypes" line item apart from 3.3 (retiring the legacy tiler — an explicit multi-sprint benchmark-then-delete process per the doc, not a one-sitting code change).

- [x] **`double_loaded_corridor`, `hub_and_spoke`, `open_core`** added to `archetypes.py` alongside `zoned_bands`. None carve a literal corridor/hub void (Phase 4 owns real circulation rects — `BandPlan.corridor_rects` stays empty here, same as 3.1a) — each only changes band *structure*: `double_loaded_corridor` anchors the public/circulation group at the facing edge then splits everyone else into two parallel wings (the perpendicular axis) instead of one deep band, alternating repeat units between them; `hub_and_spoke` gives the highest-`circulation_weight` public node its own facing-anchored band with must-adjacent spokes sorted first in the rest; `open_core` anchors the single largest-area node (any zone) at the facing edge with everyone else as one band behind it.
- [x] **`zoned_bands` refactored, not rewritten:** its floor-then-slack band allocation is now the shared `_facing_progression_bands` helper (also used by `open_core`/`hub_and_spoke`'s 2-group facing splits) plus a new `_split_rect` helper for the perpendicular-axis wing split `double_loaded_corridor` needs. All 9 pre-existing `zoned_bands` tests pass unmodified — confirmed behavior-preserving, not just assumed.
- [x] **`select_archetype`** implements the doc's rule chain in order: ≥3 same-type repeat units in a semi_private/private zone plus a corridor-spine node → `double_loaded_corridor`; a public node with ≥3 MUST-adjacent spokes → `hub_and_spoke`; one node ≥50% of the program's total area → `open_core`; else `zoned_bands`. `RequirementsSpec.layout_style` (new optional field, closed `Literal` over the 4 archetype keys, same "reject don't invent" posture as every other enum in that file) lets a caller override the rule chain explicitly.
- [x] **Caught a real false positive before committing, not after:** the doc's literal selector rule ("≥3 repeat units + a circulation node") reads `program_graph.py`'s full `_CIRCULATION_TYPES` set, which includes `entry` — and `program_completion.ensure_entry` auto-injects an entry node into virtually every program, residential ones included. Ran all 5 real requirement fixtures through `select_archetype` directly (not assumed safe): `4bhk` (3 bedrooms + auto-entry) and `clinic` (3 `study` + auto-entry) both silently flipped to `double_loaded_corridor` under the naive rule — an unrequested behavior change to already-shipped residential/clinic generation the moment this file gained a second archetype. Fixed by gating on a genuine `_CORRIDOR_SPINE_TYPES` node (`hallway`/`corridor`/`passage`/`passageway` — NOT `entry`/`foyer`/`lobby`/`staircase`) instead of "any circulation node." Re-verified all 5 fixtures resolve to `zoned_bands` again; a permanent regression test (`test_select_archetype_does_not_flip_existing_residential_fixtures_with_three_plus_bedrooms`) pins the exact case.
- [x] **New end-to-end fixtures (office/school/warehouse/restaurant) were NOT added**, despite the doc's acceptance section listing them: `PlanRoom.type` in `schemas/layout_plan.py` is still the closed 12-value `RoomType` enum (the same "Known contract limit" 3.1a already flagged, migration-order item 4 from Phase 1.2, still not started) — `generate_plan()` would raise constructing `PlanRoom(type=RoomType(need.type))` for any free-string type like `"consultation_room"`. All 4 new archetypes are proven instead via synthetic `EngineProgram` unit tests, the identical boundary 3.1a already established for `zoned_bands`.
- [x] **Tests:** `test_archetypes.py` grew from 9 to 23 tests — per-archetype structure/tiling/fallback checks for all 3 new archetypes, the selector's 4 rule branches plus explicit-override, the corridor-spine false-positive regression, and a "reasons always non-empty" sweep.
- [x] **Verification:** `pytest app/tests -q` — **802 passed, 3 expected live-LM skips, 0 failed** (779 baseline + 23 archetype tests). Hypothesis property gate re-run in isolation, still green (none of the 5 real fixtures exercise the new archetypes, so this only confirms zero regression to the existing residential path).
- [ ] **Not done (by design):** 3.3 (wrap the legacy tiler as a 5th "tiled" archetype, benchmark both paths for 2 sprints, then delete) — a monitoring/timeline process per the doc, not implementable as a single code change. Phase 4 (real circulation geometry, corridor/hub voids as actual rects) and the `PlanRoom.type` closed-enum migration remain the two concrete blockers before any non-residential program can run through `generate_plan()` end-to-end.

### MVP Phase 8 — polygon building-boundary engine (`mvp/phase8-polygon-boundary-engine`, off `phase1/space-catalog`)

> Separate from the `archiai_engine_generalization_workflow.md` numbering above (that doc gates non-rectangular geometry as its own Phase 10.2, "only after P1–P5 are merged and benchmarked"). This is MVP-pipeline-side work — an opt-in straight-edge polygon plot/room path — found already in progress (uncommitted) on this branch and finished/committed in this session at the owner's direction.

- [x] `RequirementsSpec.plot.boundary` / `LayoutPlan` room `vertices` (schemas) — a straight-edge polygon plot or room footprint, additive: `x/y/w/h` stays the bounding box, `vertices` (when set) is the real outline; rotation must be 0 when `vertices` is set.
- [x] `polygon.py` (shapely-backed: `Polygon`/`box`/`Point`, `intersection`/`covers`/`boundary`/`area` only — no `shapely.ops.split`, triangulation, or buffering) + `polygon_subdivision.py` + `engine._generate_plan_polygon`, dispatched from `generate_plan` only when `spec.plot.boundary` is set. The rectangular path is untouched byte-for-byte; `_place_doors` is reused unchanged (confirmed shape-agnostic — it only ever reads `RoomNeed`/`Wall`/wall-length). New `shapely>=2.0,<3.0` dependency.
- [x] `_wall_length` switched Manhattan → Euclidean (`math.hypot`) since a slanted polygon-boundary wall isn't axis-aligned — a no-op for every axis-aligned wall, verified byte-identical against all 5 existing fixtures.
- [x] 23 new tests (`test_polygon_geometry.py`, `test_polygon_subdivision.py`, `test_mvp_engine_polygon.py`); full backend suite green at commit time — **811 passed, 3 expected live-LM skips, 0 failed**.
- [ ] Polygon-aware banding (archetypes) is deferred — the whole boundary subdivides as one band, matching `zoned_bands`'s own single-zone collapse case.

### Phase 1.2 migration-order item 4 — `PlanRoom.type` closed enum → validated free string (`phase3/layout-archetypes`, stacked on 3.1b-d+3.2)

> Closes the last blocker flagged three times over (Phase 1.2, Phase 2.2b, Phase 3.1a): `generate_plan()` could not emit a non-residential room, so `hub_and_spoke`/`open_core`/`double_loaded_corridor` could compute correct band structure for a program like "reception + consultation_room" but nothing could turn it into a real `LayoutPlan` — `PlanRoom(type=RoomType(need.type))` raised `ValueError` for anything outside the 12 residential values. Done at the owner's explicit request, conditioned on not breaking existing structure — traced every real consumer before editing anything, verified empirically rather than assumed at each risky step.

- [x] **`PlanRoom.type`: `RoomType` → `str` (bounded, catalog-validated at the service boundary).** Field name stays `type` (not renamed to `space_type` — avoids a breaking key rename across persisted layouts, the frontend contract, and the legacy canvas adapter). Confirmed empirically before writing any code: Pydantic normalizes a `RoomType` member passed into a plain-`str` field to its plain string value (`RoomType.bedroom` → `"bedroom"`, not `"RoomType.bedroom"`), so every existing call site that does `PlanRoom(type=RoomType.bedroom, ...)` — test fixtures included — keeps working byte-for-byte unmodified.
- [x] **Every real consumer traced and fixed, not just the construction site:** `layout_adapter.py`/`vastu.py` had `.value` access that would AttributeError on a plain str (dropped, since the value's already a string); `hard_constraints.validate` and `engine.rebuild_derived_geometry` both did `ROOM_SIZING[room.type]`, which would `KeyError` for any non-residential type — replaced with a new `catalog.min_dimensions()` lenient lookup (byte-identical to `ROOM_SIZING` for all 12 residential types — parity pinned by a parametrized test — graceful `(1.2, 1.2)` default for anything else, matching `EngineProgram._resolve_sizing`'s own established leniency). `soft_rules.py`/`export/render.py` needed **no change** — confirmed in a REPL first that plain equality/dict-key lookups against a `RoomType` member and a plain string already behave identically (`str, Enum` hash/eq compatibility), so those files were correctly left untouched rather than "fixed" speculatively.
- [x] **Added validation that didn't exist before, at the right boundary:** `program_graph.py::from_requirements`'s `spec.spaces` branch now calls `catalog.get(request.space_type)` eagerly — before this, an unknown free-string type silently fell through `to_engine_program`'s lenient `_resolve_sizing` to a made-up 3×3 m default, then either crashed building the final `PlanRoom` (pre-migration) or would have silently generated a nonsense room (post-migration, if left unvalidated). `engine.py::_build_program` catches `catalog.UnknownSpaceType` and translates it into the existing `DoesNotFitError` clarification flow (`_fit_question`'s generic fallback already handles a message with no `required_area`/`plot_area`, so this needed no router or clarification-service change) — verified live: a garbage type now returns a clean structured error instead of a 500.
- [x] **Frontend deliberately untouched** — traced `contracts.ts` and every file importing it; the one place that gates on the closed 12-value set (`mvpLayoutAdapter.ts`'s `CANONICAL_ROOM_TYPES`) already fails safe by *excluding* non-canonical rooms from the live-sync fast path, not crashing. Nothing in the UI can submit `spec.spaces` today (no such control exists), so widening `contracts.ts`'s `RoomType` union is real, additive, but out-of-scope frontend work for whenever a UI control actually needs it — not an oversight.
- [x] **Verified, not assumed, at every step:** a live 4-space clinic program (reception/waiting_room/3×consultation_room/bathroom) now generates a full, valid, zero-hard-violation `LayoutPlan` through the real `generate_plan()` entrypoint — proof the actual blocker is gone. All 5 real residential/clinic fixtures re-run through `generate_plan()` produce identical room/wall/door counts to before this change (4bhk: 14 rooms/43 walls/15 doors, matching the exact counts Phase 2.2b's own write-up recorded).
- [x] **Tests:** 20 new — `catalog.min_dimensions` parity (parametrized over all 12 `RoomType` values) + non-residential + unknown-type-default cases; `generate_plan()` end-to-end non-residential success + unknown-type rejection; `rebuild_derived_geometry` on a hand-edited non-residential room type; `hard_constraints.validate`'s `below_min_size` firing correctly for both a known non-residential type and a truly-unknown one; `from_requirements` rejecting an unknown `space_type` eagerly.
- [x] **Verification:** `pytest app/tests -q` — **822 passed** (802 baseline + 20 new), 3 expected live-LM skips, 0 failed. Frontend untouched but re-verified anyway per the "don't break anything" bar: `npx tsc --noEmit` clean, `npm test -- --run` **271 passed / 54 files**, `npm run build` clean (same pre-existing bundle-size warning as every prior phase, nothing new).
- [ ] **Not done (explicitly out of scope for this slice):** the frontend `contracts.ts`/`mvpLayoutAdapter.ts` widening described above; `schemas/layout_plan.py`'s `PlanRoom.type` migration is the only piece of Phase 1.2's migration-order item 4 that existed — the office/school/warehouse/restaurant end-to-end fixtures this unblocks were not added in this pass (nothing asked for them here; the unblocking itself was the ask).

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
| `docs/superpowers/specs/2026-05-23-sprint1-auth-design.md` | Sprint 1 detailed design spec |

---

## Contact / Ownership

Project: ArchiAI
Repo: `github.com/samarth080/archiai-saas`
Lead: samarth080
