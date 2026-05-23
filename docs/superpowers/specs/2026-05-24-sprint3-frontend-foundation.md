# Sprint 3 — Frontend Foundation: Design Spec

**Date:** 2026-05-24
**Status:** Approved
**Sprint Goal:** Wire the frontend to the Sprint 2 Project API — users can create, view, update, and delete projects from a real dashboard connected to the backend.

---

## Context

Builds on Sprint 1 (auth frontend) and Sprint 2 (Project CRUD API). The following already exist and must not be changed except where noted:

- `src/store/authStore.ts` — Zustand auth store, `useAuthStore()`, token in `localStorage`
- `src/services/auth.service.ts` — auth API calls
- `src/hooks/useAuth.ts` — `useAuth()` hook
- `src/components/ui/Button.tsx` — primary/secondary variants
- `src/components/ui/Input.tsx` — label, error, forwarded ref
- `src/App.tsx` — routing (MODIFY to add `/projects/:id`)
- `src/pages/Dashboard/index.tsx` — stub (MODIFY to full dashboard)
- `src/pages/Landing`, `Login`, `Register` — no changes

---

## Architecture

Four additions on top of the existing frontend:

1. **Shared Axios instance** (`src/services/api.ts`) — configured with `VITE_API_URL` base URL, injects `Authorization: Bearer <token>` from the auth store on every request, redirects to `/login` on 401.

2. **Project service** (`src/services/project.service.ts`) — five typed functions wrapping the project endpoints. All functions use the shared Axios instance.

3. **Dashboard rebuild** (`src/pages/Dashboard/index.tsx`) — sidebar + grid layout. Fetches the project list on mount with local `useState`/`useEffect`. No Zustand store — each page owns its own data.

4. **Project workspace page** (`src/pages/Project/index.tsx`) — fetched by ID on mount. Top bar with project name, back link, inline edit, and delete. Canvas placeholder for Sprint 4.

State management: local `useState` only. No new Zustand stores. No new npm dependencies.

---

## File Map

```
frontend/src/
├── services/
│   ├── api.ts                          CREATE
│   └── project.service.ts              CREATE
├── components/
│   └── projects/
│       ├── CreateProjectModal.tsx       CREATE
│       └── ProjectCard.tsx              CREATE
├── pages/
│   ├── Dashboard/
│   │   └── index.tsx                   MODIFY (full rebuild)
│   └── Project/
│       └── index.tsx                   CREATE
└── App.tsx                             MODIFY (add /projects/:id route)
```

---

## Shared Axios Instance (`src/services/api.ts`)

```typescript
import axios from 'axios'
import { useAuthStore } from '../store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

---

## Project Service (`src/services/project.service.ts`)

```typescript
import api from './api'

export interface Project {
  id: string
  user_id: string
  title: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface CreateProjectData {
  title: string
  description?: string
}

export interface UpdateProjectData {
  title?: string
  description?: string
}

const projectService = {
  list: (): Promise<Project[]> =>
    api.get('/api/projects').then((r) => r.data),

  get: (id: string): Promise<Project> =>
    api.get(`/api/projects/${id}`).then((r) => r.data),

  create: (data: CreateProjectData): Promise<Project> =>
    api.post('/api/projects', data).then((r) => r.data),

  update: (id: string, data: UpdateProjectData): Promise<Project> =>
    api.put(`/api/projects/${id}`, data).then((r) => r.data),

  delete: (id: string): Promise<void> =>
    api.delete(`/api/projects/${id}`).then(() => undefined),
}

export default projectService
```

---

## Components

### `ProjectCard` (`src/components/projects/ProjectCard.tsx`)

Props:
```typescript
interface ProjectCardProps {
  project: Project
  onClick: () => void
}
```

Displays: title, description (truncated to 1 line, or "No description"), formatted `created_at` date. Entire card is clickable — calls `onClick`.

### `CreateProjectModal` (`src/components/projects/CreateProjectModal.tsx`)

Props:
```typescript
interface CreateProjectModalProps {
  onClose: () => void
  onCreated: (project: Project) => void
}
```

Fields:
- Title (required, min 1 char) — validated with React Hook Form
- Description (optional textarea)

Submit calls `projectService.create()`. On success calls `onCreated(project)` and closes. On error shows inline error message below the form. Cancel button calls `onClose()`.

The modal renders as a fixed overlay with a centered white dialog. Background click does not close (prevents accidental dismissal).

---

## Dashboard Page (`src/pages/Dashboard/index.tsx`)

Layout: two-column with fixed left sidebar and scrollable right content area.

**Sidebar (left, fixed width ~200px, dark background):**
- ArchiAI logo/wordmark at top
- Navigation: "Projects" link (active state)
- Bottom: user name + Logout button

**Main area (right):**
- Header row: "Projects" heading + "+ New Project" button
- Loading state: spinner while fetching
- Empty state: centered message "No projects yet. Click '+ New Project' to create your first."
- Error state: red inline message if fetch fails
- Grid: 3-column responsive card grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`)

**Data flow:**
```
mount → setLoading(true) → projectService.list()
  → setProjects(data) → setLoading(false)
  → on error: setError(message) → setLoading(false)

"+ New Project" → setShowModal(true)
modal onCreated(project) → setProjects(prev => [project, ...prev]) → setShowModal(false)

card onClick → navigate(`/projects/${project.id}`)
```

---

## Project Workspace Page (`src/pages/Project/index.tsx`)

Route: `/projects/:id` (protected)

**Data flow:**
```
mount → projectService.get(id)
  → setProject(data)
  → on 404: navigate('/dashboard')
  → on error: setError(message)
```

**Layout:** same sidebar as Dashboard + main content area.

**Top bar (inside main area):**
- Back link: "← Projects" → navigate('/dashboard')
- Project title (display mode: plain text; edit mode: text input)
- "Edit" button → enters edit mode
- "Delete" button → `window.confirm('Delete this project?')` → `projectService.delete(id)` → `navigate('/dashboard')`

**Edit mode:**
- Title becomes an `<input>` (pre-filled)
- Description becomes a `<textarea>` (pre-filled, empty if null)
- "Save" button → `projectService.update(id, { title, description })` → updates local state → exits edit mode
- "Cancel" button → exits edit mode without saving
- Inline error below form if save fails

**Canvas placeholder (below top bar):**
```tsx
<div className="flex-1 bg-gray-100 flex items-center justify-center flex-col gap-2">
  <span className="text-4xl">🏗️</span>
  <p className="text-gray-400 text-sm">3D canvas coming in Sprint 4</p>
</div>
```

---

## Routing (`src/App.tsx`)

Add one new protected route:

```tsx
<Route element={<ProtectedRoute />}>
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/projects/:id" element={<Project />} />
</Route>
```

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Fetch projects fails | Red error message inline in dashboard, no crash |
| Create project fails | Error shown below modal form, modal stays open |
| Project not found (404) | Redirect to `/dashboard` |
| Project update fails | Error shown below edit form |
| Any 401 response | Auth store logout → redirect to `/login` |

Errors use the backend's `{ error, code, status }` shape — display `error` string to the user.

---

## Definition of Done (Sprint 3)

- [ ] Shared Axios instance injects Bearer token on every request
- [ ] 401 responses log the user out and redirect to `/login`
- [ ] Dashboard shows real projects fetched from `GET /api/projects`
- [ ] "+ New Project" opens a modal — creating a project calls `POST /api/projects` and adds it to the grid
- [ ] Clicking a project card navigates to `/projects/:id`
- [ ] Project page loads project data from `GET /api/projects/:id`
- [ ] Edit mode updates title/description via `PUT /api/projects/:id`
- [ ] Delete button removes the project and redirects to dashboard
- [ ] Empty state shown when user has no projects
- [ ] Loading state shown while fetching
- [ ] Error states shown inline (no crashes)
- [ ] `docker-compose up` serves the working frontend
