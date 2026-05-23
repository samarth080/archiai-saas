# Sprint 3 — Frontend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the ArchiAI frontend to the backend Project API so users can create, list, view, edit, and delete projects from a real dashboard.

**Architecture:** A shared Axios instance with an auth interceptor feeds a typed project service. The Dashboard is rebuilt with a sidebar + card grid layout that fetches real data. A new Project workspace page handles viewing, editing, and deleting a single project. All state is local (`useState`) — no new Zustand stores.

**Tech Stack:** React 18, TypeScript, Axios, React Hook Form, React Router v6, Tailwind CSS, Zustand (auth store only)

---

## File Map

```
frontend/src/
├── services/
│   ├── api.ts                          CREATE — shared Axios instance with auth interceptor
│   └── project.service.ts              CREATE — list, get, create, update, delete + types
├── components/
│   └── projects/
│       ├── ProjectCard.tsx             CREATE — card with title, description, date, click handler
│       └── CreateProjectModal.tsx      CREATE — modal form with title + description
├── pages/
│   ├── Dashboard/
│   │   └── index.tsx                   MODIFY — full rebuild: sidebar + grid, fetch projects
│   └── Project/
│       └── index.tsx                   CREATE — workspace page: header, inline edit, delete, canvas placeholder
└── App.tsx                             MODIFY — add /projects/:id protected route
```

**No new npm dependencies.** All packages (axios, react-hook-form, react-router-dom, zustand) are already in `frontend/package.json`.

**Note on testing:** The frontend has no test runner configured (no vitest, no jest). Verification is done by TypeScript compilation (`npm run build` inside the `frontend/` container or locally) and manual browser testing.

---

## Task 1: Shared Axios Instance

**Files:**
- Create: `frontend/src/services/api.ts`

- [ ] **Step 1: Create `frontend/src/services/api.ts`**

```typescript
import axios from 'axios'

import { useAuthStore } from '../store/authStore'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
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

- [ ] **Step 2: Verify TypeScript accepts the file**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors related to `api.ts`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.ts
git commit -m "feat(sprint3): add shared Axios instance with auth interceptor"
```

---

## Task 2: Project Service

**Files:**
- Create: `frontend/src/services/project.service.ts`

- [ ] **Step 1: Create `frontend/src/services/project.service.ts`**

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

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/project.service.ts
git commit -m "feat(sprint3): add project service (list, get, create, update, delete)"
```

---

## Task 3: ProjectCard Component

**Files:**
- Create: `frontend/src/components/projects/ProjectCard.tsx`

- [ ] **Step 1: Create `frontend/src/components/projects/ProjectCard.tsx`**

```typescript
import { Project } from '../../services/project.service'

interface ProjectCardProps {
  project: Project
  onClick: () => void
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function ProjectCard({ project, onClick }: ProjectCardProps) {
  return (
    <button
      onClick={onClick}
      className="text-left w-full bg-white border border-gray-200 rounded-lg p-4 hover:border-indigo-400 hover:shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500"
    >
      <h3 className="font-semibold text-gray-900 truncate mb-1">{project.title}</h3>
      <p className="text-sm text-gray-500 truncate mb-3">
        {project.description ?? 'No description'}
      </p>
      <p className="text-xs text-gray-400">Created {formatDate(project.created_at)}</p>
    </button>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/projects/ProjectCard.tsx
git commit -m "feat(sprint3): add ProjectCard component"
```

---

## Task 4: CreateProjectModal Component

**Files:**
- Create: `frontend/src/components/projects/CreateProjectModal.tsx`

- [ ] **Step 1: Create `frontend/src/components/projects/CreateProjectModal.tsx`**

```typescript
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '../ui/Button'
import { Input } from '../ui/Input'
import projectService, { CreateProjectData, Project } from '../../services/project.service'

interface CreateProjectModalProps {
  onClose: () => void
  onCreated: (project: Project) => void
}

export function CreateProjectModal({ onClose, onCreated }: CreateProjectModalProps) {
  const [apiError, setApiError] = useState('')
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<CreateProjectData>()

  async function onSubmit(data: CreateProjectData) {
    setApiError('')
    try {
      const project = await projectService.create(data)
      onCreated(project)
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        'Failed to create project'
      setApiError(message)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-bold text-gray-900 mb-4">New Project</h2>
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
          <Input
            label="Title"
            placeholder="My project"
            error={errors.title?.message}
            {...register('title', { required: 'Title is required' })}
          />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-700" htmlFor="description">
              Description
            </label>
            <textarea
              id="description"
              placeholder="Optional description"
              rows={3}
              className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              {...register('description')}
            />
          </div>
          {apiError && <p className="text-sm text-red-600">{apiError}</p>}
          <div className="flex gap-3 justify-end">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              Create
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/projects/CreateProjectModal.tsx
git commit -m "feat(sprint3): add CreateProjectModal component"
```

---

## Task 5: Dashboard Page Rebuild

**Files:**
- Modify: `frontend/src/pages/Dashboard/index.tsx`

- [ ] **Step 1: Replace the entire contents of `frontend/src/pages/Dashboard/index.tsx`**

```typescript
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '../../components/ui/Button'
import { CreateProjectModal } from '../../components/projects/CreateProjectModal'
import { ProjectCard } from '../../components/projects/ProjectCard'
import { useAuth } from '../../hooks/useAuth'
import projectService, { Project } from '../../services/project.service'

export default function Dashboard() {
  const { user, logOut } = useAuth()
  const navigate = useNavigate()

  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    projectService
      .list()
      .then(setProjects)
      .catch(() => setError('Failed to load projects'))
      .finally(() => setLoading(false))
  }, [])

  function handleCreated(project: Project) {
    setProjects((prev) => [project, ...prev])
    setShowModal(false)
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-48 bg-slate-800 text-white flex flex-col flex-shrink-0">
        <div className="px-4 py-5">
          <span className="text-lg font-bold">ArchiAI</span>
        </div>
        <nav className="flex-1 px-2">
          <div className="px-2 py-2 rounded bg-white/10 text-sm font-medium">
            📁 Projects
          </div>
        </nav>
        <div className="px-4 py-4 border-t border-white/10">
          <p className="text-sm text-slate-300 truncate mb-2">{user?.name}</p>
          <Button variant="secondary" className="w-full text-sm py-1" onClick={logOut}>
            Logout
          </Button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <Button onClick={() => setShowModal(true)}>+ New Project</Button>
        </div>

        {loading && (
          <div className="flex items-center justify-center h-40">
            <svg className="animate-spin h-8 w-8 text-indigo-600" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
          </div>
        )}

        {!loading && error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}

        {!loading && !error && projects.length === 0 && (
          <div className="flex flex-col items-center justify-center h-40 text-gray-400">
            <p className="text-lg mb-2">No projects yet</p>
            <p className="text-sm">Click &ldquo;+ New Project&rdquo; to create your first.</p>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => navigate(`/projects/${project.id}`)}
              />
            ))}
          </div>
        )}
      </main>

      {showModal && (
        <CreateProjectModal
          onClose={() => setShowModal(false)}
          onCreated={handleCreated}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard/index.tsx
git commit -m "feat(sprint3): rebuild Dashboard with sidebar + project grid wired to API"
```

---

## Task 6: Project Workspace Page

**Files:**
- Create: `frontend/src/pages/Project/index.tsx`

- [ ] **Step 1: Create `frontend/src/pages/Project/index.tsx`**

```typescript
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'

import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import projectService, { Project, UpdateProjectData } from '../../services/project.service'

export default function ProjectPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [editing, setEditing] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [deleting, setDeleting] = useState(false)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UpdateProjectData>()

  useEffect(() => {
    if (!id) return
    projectService
      .get(id)
      .then((p) => {
        setProject(p)
        reset({ title: p.title, description: p.description ?? '' })
      })
      .catch((err: unknown) => {
        const status = (err as { response?: { status?: number } })?.response?.status
        if (status === 404 || status === 403) {
          navigate('/dashboard')
        } else {
          setError('Failed to load project')
        }
      })
      .finally(() => setLoading(false))
  }, [id, navigate, reset])

  async function onSave(data: UpdateProjectData) {
    if (!id) return
    setSaveError('')
    try {
      const updated = await projectService.update(id, data)
      setProject(updated)
      setEditing(false)
    } catch {
      setSaveError('Failed to save changes')
    }
  }

  function handleCancelEdit() {
    if (project) reset({ title: project.title, description: project.description ?? '' })
    setSaveError('')
    setEditing(false)
  }

  async function handleDelete() {
    if (!id) return
    if (!window.confirm('Delete this project? This cannot be undone.')) return
    setDeleting(true)
    try {
      await projectService.delete(id)
      navigate('/dashboard')
    } catch {
      setDeleting(false)
      alert('Failed to delete project')
    }
  }

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <svg className="animate-spin h-8 w-8 text-indigo-600" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen items-center justify-center flex-col gap-4">
        <p className="text-red-600">{error}</p>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>
          Back to Projects
        </Button>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-48 bg-slate-800 text-white flex flex-col flex-shrink-0">
        <div className="px-4 py-5">
          <span className="text-lg font-bold">ArchiAI</span>
        </div>
        <nav className="flex-1 px-2">
          <button
            onClick={() => navigate('/dashboard')}
            className="w-full text-left px-2 py-2 rounded text-sm text-slate-300 hover:bg-white/10 transition-colors"
          >
            📁 Projects
          </button>
        </nav>
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm text-indigo-600 hover:underline mb-1 block"
          >
            ← Projects
          </button>

          {editing ? (
            <form onSubmit={handleSubmit(onSave)} className="flex flex-col gap-3 mt-2">
              <Input
                label="Title"
                error={errors.title?.message}
                {...register('title', { required: 'Title is required' })}
              />
              <div className="flex flex-col gap-1">
                <label className="text-sm font-medium text-gray-700" htmlFor="description">
                  Description
                </label>
                <textarea
                  id="description"
                  rows={2}
                  className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                  {...register('description')}
                />
              </div>
              {saveError && <p className="text-sm text-red-600">{saveError}</p>}
              <div className="flex gap-2">
                <Button type="submit" loading={isSubmitting}>
                  Save
                </Button>
                <Button type="button" variant="secondary" onClick={handleCancelEdit}>
                  Cancel
                </Button>
              </div>
            </form>
          ) : (
            <div className="flex items-start justify-between">
              <div>
                <h1 className="text-xl font-bold text-gray-900">{project?.title}</h1>
                {project?.description && (
                  <p className="text-sm text-gray-500 mt-1">{project.description}</p>
                )}
              </div>
              <div className="flex gap-2 ml-4">
                <Button variant="secondary" onClick={() => setEditing(true)}>
                  Edit
                </Button>
                <Button
                  variant="secondary"
                  loading={deleting}
                  onClick={handleDelete}
                  className="!text-red-600 !border-red-300 hover:!bg-red-50"
                >
                  Delete
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Canvas placeholder */}
        <div className="flex-1 flex items-center justify-center flex-col gap-3 bg-gray-100">
          <span className="text-5xl">🏗️</span>
          <p className="text-gray-400 text-sm">3D canvas coming in Sprint 4</p>
        </div>
      </main>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Project/index.tsx
git commit -m "feat(sprint3): add Project workspace page with edit, delete, canvas placeholder"
```

---

## Task 7: Update App.tsx Routing

**Files:**
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Replace the entire contents of `frontend/src/App.tsx`**

```typescript
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import ProjectPage from './pages/Project'
import Register from './pages/Register'
import { useAuthStore } from './store/authStore'

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Outlet />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects/:id" element={<ProjectPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 2: Verify TypeScript**

```bash
cd frontend
npx tsc --noEmit
```

Expected: no errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat(sprint3): add /projects/:id protected route"
```

---

## Task 8: Manual End-to-End Verification

- [ ] **Step 1: Start the full stack**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
docker-compose up --build
```

Wait for all three services (db, backend, frontend) to be ready.

- [ ] **Step 2: Verify dashboard loads projects**

1. Open http://localhost:5173
2. Register a new account (or log in if one exists)
3. Confirm the dashboard shows the sidebar + "Projects" heading + "+ New Project" button
4. Confirm "No projects yet" empty state is visible

- [ ] **Step 3: Verify project creation**

1. Click "+ New Project"
2. Confirm modal appears with Title and Description fields
3. Enter title "Test Office Layout", leave description empty
4. Click "Create"
5. Confirm modal closes and the new project card appears in the grid

- [ ] **Step 4: Verify project workspace**

1. Click the project card
2. Confirm navigation to `/projects/:id`
3. Confirm title "Test Office Layout" appears in the top bar
4. Confirm "← Projects" back link works
5. Confirm "🏗️ 3D canvas coming in Sprint 4" placeholder is visible

- [ ] **Step 5: Verify edit**

1. Click "Edit" on the project page
2. Change title to "Updated Office Layout"
3. Click "Save"
4. Confirm title updates without page reload

- [ ] **Step 6: Verify delete**

1. Click "Delete"
2. Confirm browser confirmation dialog appears
3. Confirm OK navigates back to dashboard
4. Confirm the deleted project is no longer in the grid

- [ ] **Step 7: Verify scoping**

1. Register a second account in a private/incognito window
2. Confirm the second account's dashboard shows no projects
3. Confirm the first account's projects are not visible to the second account

---

## Task 9: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark Sprint 3 complete in CLAUDE.md**

Find:
```markdown
### Sprint 3 — Frontend Foundation ⏳ Not Started
```

Replace with:
```markdown
### Sprint 3 — Frontend Foundation ✅ Complete
- [x] Shared Axios instance with Bearer token interceptor and 401 auto-logout
- [x] Project service (list, get, create, update, delete)
- [x] Dashboard rebuilt: sidebar + responsive project card grid
- [x] Create Project modal with title + optional description
- [x] Project workspace page with inline edit, delete, canvas placeholder
- [x] /projects/:id protected route added
- [x] Loading, empty, and error states throughout
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: mark Sprint 3 complete in CLAUDE.md"
```

---

## Self-Review

**Spec coverage:**
- ✅ Shared Axios instance with auth interceptor — Task 1
- ✅ 401 → logout + redirect to /login — Task 1
- ✅ Project service (all 5 functions) — Task 2
- ✅ ProjectCard component — Task 3
- ✅ CreateProjectModal (title required, description optional, error handling) — Task 4
- ✅ Dashboard: sidebar + grid, loading/empty/error states, fetch on mount — Task 5
- ✅ Create project → add to front of list without re-fetch — Task 5 (`handleCreated`)
- ✅ Project workspace page: fetch on mount, 404 → redirect — Task 6
- ✅ Inline edit with Save/Cancel — Task 6
- ✅ Delete with `window.confirm` → navigate to dashboard — Task 6
- ✅ `/projects/:id` protected route — Task 7
- ✅ End-to-end manual verification — Task 8
- ✅ CLAUDE.md updated — Task 9

**Type consistency:** `Project`, `CreateProjectData`, `UpdateProjectData` defined in Task 2 and used consistently in Tasks 3, 4, 5, 6. `onCreated: (project: Project) => void` in modal matches `handleCreated` signature in Dashboard.

**No placeholders found.**
