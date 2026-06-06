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

### Sprint 13 — Smarter Layouts, Pattern Learning, and Better Canvas ⏳ In Progress

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
- [ ] Task 12: Final checks and sprint completion

- [x] Sprint 13 implementation plan created at `docs/superpowers/plans/2026-06-07-sprint13-smarter-layouts-pattern-canvas.md`
- [x] Pattern data validation keeps low-quality scraped data from influencing generation
- [x] Normalized pattern vocabulary maps messy scraped terms to internal room/building types
- [x] Pattern-weighted generation improves room sizes, zones, adjacency, and layout metadata without paid AI APIs
- [x] Canvas visualization improves readability while preserving editing, save, export, and share behavior
- [x] Non-AI pattern data workflow documented at `docs/PATTERN_DATA_WORKFLOW.md`

Deferred beyond Sprint 13:
- Paid AI API integration
- OpenAI, Claude, Gemini, or local model integration
- AI model training or fine-tuning
- CAD/BIM export and structural validation
- Advanced spatial optimization
- Public scraper/source-management workflow for normal users

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
