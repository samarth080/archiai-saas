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
- [x] Dashboard page (protected, stub)
- [x] Zustand auth store
- [x] ProtectedRoute + PublicOnlyRoute wrappers
- [x] `docker-compose up` runs full stack

### Sprint 2 — Backend Foundation ✅ Complete
- [x] Global error handler returns `{ error, code, status }` for all HTTPExceptions
- [x] RequestValidationError also returns `{ error, code, status }` shape (422)
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
- [x] 401 responses log the user out and redirect to `/login`
- [x] Dashboard rebuilt: sidebar + responsive card grid + real data from `GET /api/projects`
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
- [x] 9 prompt service tests + 8 layout service tests + 1 new store test (18 new tests)
- [x] `npx tsc --noEmit` passes with zero errors
- [x] No DB persistence (Design + DesignVersion deferred to Sprint 7)

### Sprint 6 — 3D Editing Workflow ⏳ Not Started
### Sprint 7 — Database and Project Management ⏳ Not Started
### Sprint 8 — Prompt Refinement ⏳ Not Started
### Sprint 9 — Team Collaboration, Version Control, and Logging ⏳ Not Started
### Sprint 10 — Web Scraper and Data Pipeline ⏳ Not Started
### Sprint 11 — AI / Layout Improvement ⏳ Not Started
### Sprint 12 — Export, Share, and Polish ⏳ Not Started

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
