# Sprint 9A — Version History & Restore Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users can open a version history drawer from the Project page, browse all saved design versions with name/type/date, and restore any version into the canvas as unsaved changes.

**Architecture:** A new `GET /api/design/version/{version_id}` backend endpoint fetches a single `DesignVersion` row and returns its `layout_json` as a `GenerateResponse` (the same shape the canvas store already consumes). The frontend adds a `VersionHistoryDrawer` overlay component that lists versions via the existing `projectService.versions()` call, then fetches the full layout for whichever version the user chooses to restore and calls `canvasStore.loadLayout()`.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic v2, pytest, React 18, TypeScript, Zustand, Vitest, React Testing Library, happy-dom.

**Spec:** [docs/superpowers/specs/2026-05-29-sprint9a-version-history-design.md](../specs/2026-05-29-sprint9a-version-history-design.md)

**Branch:** `sprint-9a/version-history` (already created off `main`/Sprint 7 state)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/app/api/designs/router.py` | MODIFY | Add `GET /version/{version_id}` endpoint |
| `backend/app/tests/test_designs.py` | MODIFY | 3 new endpoint tests |
| `frontend/src/services/design.service.ts` | MODIFY | Add `fetchVersion` function |
| `frontend/src/components/canvas/VersionHistoryDrawer.tsx` | CREATE | Overlay drawer component |
| `frontend/src/components/canvas/VersionHistoryDrawer.test.tsx` | CREATE | 2 RTL tests for the drawer |
| `frontend/src/pages/Project/index.tsx` | MODIFY | History button + drawer mount |
| `CLAUDE.md` | MODIFY | Mark Sprint 9A complete |

**Note:** `frontend/src/pages/Project/index.test.tsx` does **not** exist on this branch (it is on the unmerged Sprint 8 branch). The History-button tests live in `VersionHistoryDrawer.test.tsx` to keep new work self-contained.

---

## Pre-flight

```bash
git branch --show-current   # must be: sprint-9a/version-history
```

Verify baseline tests pass:

```bash
cd backend && pytest -q 2>&1 | tail -3
# expected: 84 passed
cd frontend && npm test 2>&1 | tail -3
# expected: 24 passed (canvasStore + apiError tests)
```

If anything is red, stop and fix before starting.

---

### Task 1: Backend — `GET /api/design/version/{version_id}`

**Files:**
- Modify: `backend/app/api/designs/router.py`
- Modify: `backend/app/tests/test_designs.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_designs.py`:

```python
async def test_fetch_version_returns_correct_layout(client: AsyncClient):
    token = await _register_and_token(client, "fetch-version@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Version Fetch Project", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )
    design_id = generated.json()["designId"]
    version_id = generated.json()["designVersionId"]

    response = await client.get(
        f"/api/design/version/{version_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["designId"] == design_id
    assert data["designVersionId"] == version_id
    assert isinstance(data["rooms"], list)
    assert len(data["rooms"]) > 0


async def test_fetch_version_wrong_user_returns_403(client: AsyncClient):
    token_a = await _register_and_token(client, "version-owner@example.com")
    token_b = await _register_and_token(client, "version-intruder@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Protected Version Project", "description": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project.json()["id"], "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    version_id = generated.json()["designVersionId"]

    response = await client.get(
        f"/api/design/version/{version_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


async def test_fetch_version_not_found_returns_404(client: AsyncClient):
    token = await _register_and_token(client, "version-404@example.com")

    response = await client.get(
        "/api/design/version/nonexistent-version-id",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && pytest app/tests/test_designs.py::test_fetch_version_returns_correct_layout -v
```

Expected: `FAIL` — 404 or 405 (endpoint not registered).

- [ ] **Step 3: Implement the endpoint**

In `backend/app/api/designs/router.py`, add the following imports at the top (merge with existing imports — do not duplicate):

```python
from app.models.design import Design
from app.models.design_version import DesignVersion
```

Then append this endpoint at the bottom of the file:

```python
@router.get("/version/{version_id}", response_model=GenerateResponse)
async def fetch_version(
    version_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> GenerateResponse:
    version = await db.get(DesignVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Version not found")

    design = await db.get(Design, version.design_id)
    if design is None or design.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")

    layout = {
        k: v
        for k, v in version.layout_json.items()
        if k not in ("designId", "designVersionId")
    }
    return GenerateResponse(
        **layout,
        designId=design.id,
        designVersionId=version.id,
    )
```

- [ ] **Step 4: Run all three new tests**

```bash
cd backend && pytest \
  app/tests/test_designs.py::test_fetch_version_returns_correct_layout \
  app/tests/test_designs.py::test_fetch_version_wrong_user_returns_403 \
  app/tests/test_designs.py::test_fetch_version_not_found_returns_404 -v
```

Expected: 3 PASS.

- [ ] **Step 5: Run the full backend suite**

```bash
cd backend && pytest -q 2>&1 | tail -3
```

Expected: 0 failures (87 or more total).

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/designs/router.py backend/app/tests/test_designs.py
git commit -m "feat(sprint9a): GET /api/design/version/{version_id} endpoint"
```

---

### Task 2: Frontend — `fetchVersion` service function

**Files:**
- Modify: `frontend/src/services/design.service.ts`

- [ ] **Step 1: Add `fetchVersion` to `design.service.ts`**

Append to `frontend/src/services/design.service.ts`:

```typescript
export async function fetchVersion(versionId: string): Promise<GenerateResponse> {
  const { data } = await api.get<GenerateResponse>(`/api/design/version/${versionId}`)
  return data
}
```

- [ ] **Step 2: Verify TypeScript is clean**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/design.service.ts
git commit -m "feat(sprint9a): add fetchVersion to design service"
```

---

### Task 3: Frontend — `VersionHistoryDrawer` component with tests

**Files:**
- Create: `frontend/src/components/canvas/VersionHistoryDrawer.tsx`
- Create: `frontend/src/components/canvas/VersionHistoryDrawer.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/canvas/VersionHistoryDrawer.test.tsx`:

```tsx
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { VersionHistoryDrawer } from './VersionHistoryDrawer'
import api from '../../services/api'
import { useCanvasStore, INITIAL_ROOMS, DEFAULT_FLOOR, DEFAULT_FLOOR_HEIGHT } from '../../store/canvasStore'

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../../services/project.service', () => ({
  default: {
    versions: vi.fn(),
  },
}))

import projectService from '../../services/project.service'

const VERSION_FIXTURES = [
  {
    id: 'v1',
    design_id: 'd1',
    project_id: 'p1',
    version_number: 2,
    version_name: 'Client review',
    version_type: 'manual',
    change_summary: 'Moved rooms',
    created_by: 'u1',
    created_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(), // 1h ago
  },
  {
    id: 'v2',
    design_id: 'd1',
    project_id: 'p1',
    version_number: 1,
    version_name: 'Generated layout',
    version_type: 'generated',
    change_summary: null,
    created_by: 'u1',
    created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2h ago
  },
]

const DESIGN_FIXTURE = {
  version: '1.0',
  designId: 'd1',
  designVersionId: 'v1',
  metadata: { prompt: 'test', building_type: 'apartment', room_count: 1 },
  building: { floorHeight: 3.2 },
  floors: [],
  rooms: [],
}

beforeEach(() => {
  vi.mocked(api.get).mockReset()
  vi.mocked(projectService.versions).mockReset()
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({
      ...r,
      floorId: DEFAULT_FLOOR.id,
      floorLevel: DEFAULT_FLOOR.level,
      position: { ...r.position },
      size: { ...r.size },
      rotation: { ...r.rotation },
    })),
    floors: [DEFAULT_FLOOR],
    selectedFloor: 0,
    floorHeight: DEFAULT_FLOOR_HEIGHT,
    designId: null,
    designVersionId: null,
    layoutMetadata: {},
    selectedId: null,
    snapToGrid: false,
    gridSize: 1,
    saveStatus: 'saved',
    lastSavedAt: null,
    activityLog: [],
  })
})

describe('VersionHistoryDrawer', () => {
  it('renders version rows when open', async () => {
    vi.mocked(projectService.versions).mockResolvedValue(VERSION_FIXTURES)

    render(
      <VersionHistoryDrawer
        projectId="p1"
        open={true}
        onClose={vi.fn()}
      />
    )

    await waitFor(() =>
      expect(screen.getByText('Client review')).toBeInTheDocument()
    )
    expect(screen.getByText('Generated layout')).toBeInTheDocument()
    expect(screen.getAllByRole('button', { name: 'Restore' })).toHaveLength(2)
  })

  it('calls fetchVersion and closes drawer on Restore click', async () => {
    vi.mocked(projectService.versions).mockResolvedValue(VERSION_FIXTURES)
    vi.mocked(api.get).mockResolvedValue({ data: DESIGN_FIXTURE })
    const onClose = vi.fn()

    render(
      <VersionHistoryDrawer
        projectId="p1"
        open={true}
        onClose={onClose}
      />
    )

    await waitFor(() => screen.getByText('Client review'))

    const restoreButtons = screen.getAllByRole('button', { name: 'Restore' })
    await userEvent.click(restoreButtons[0])

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/design/version/v1')
    )
    await waitFor(() => expect(onClose).toHaveBeenCalled())
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npm test -- src/components/canvas/VersionHistoryDrawer.test.tsx
```

Expected: FAIL — `VersionHistoryDrawer` module not found.

- [ ] **Step 3: Implement `VersionHistoryDrawer`**

Create `frontend/src/components/canvas/VersionHistoryDrawer.tsx`:

```tsx
import { useEffect, useState } from 'react'
import projectService, { ProjectVersion } from '../../services/project.service'
import { fetchVersion } from '../../services/design.service'
import { useCanvasStore } from '../../store/canvasStore'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

const TYPE_BADGE: Record<string, string> = {
  generated: 'bg-indigo-100 text-indigo-700',
  manual: 'bg-emerald-100 text-emerald-700',
  refined: 'bg-amber-100 text-amber-700',
  duplicate: 'bg-gray-100 text-gray-600',
}

const TYPE_LABEL: Record<string, string> = {
  generated: 'Generated',
  manual: 'Manual save',
  refined: 'Refined',
  duplicate: 'Duplicate',
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function VersionHistoryDrawer({ projectId, open, onClose }: Props) {
  const [versions, setVersions] = useState<ProjectVersion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [restoringId, setRestoringId] = useState<string | null>(null)
  const loadLayout = useCanvasStore((s) => s.loadLayout)

  useEffect(() => {
    if (!open) return
    setLoading(true)
    setError(null)
    projectService
      .versions(projectId)
      .then(setVersions)
      .catch(() => setError('Failed to load version history.'))
      .finally(() => setLoading(false))
  }, [open, projectId])

  async function handleRestore(versionId: string) {
    setRestoringId(versionId)
    try {
      const result = await fetchVersion(versionId)
      loadLayout(result)
      onClose()
    } catch {
      setError('Failed to restore version.')
    } finally {
      setRestoringId(null)
    }
  }

  if (!open) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        aria-hidden="true"
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Version history"
        className="fixed inset-y-0 right-0 z-50 w-80 bg-white shadow-xl flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
          <h2 className="text-sm font-semibold text-gray-900">Version history</h2>
          <button
            type="button"
            aria-label="Close history"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
          {loading && <p className="text-sm text-gray-400">Loading…</p>}
          {error && <p className="text-sm text-red-500">{error}</p>}
          {!loading && !error && versions.length === 0 && (
            <p className="text-sm text-gray-400">No versions saved yet.</p>
          )}
          {versions.map((v) => (
            <div
              key={v.id}
              className="rounded border border-gray-200 p-3 flex flex-col gap-1"
            >
              <div className="flex items-start justify-between gap-2">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {v.version_name ?? 'Untitled version'}
                </span>
                <button
                  type="button"
                  aria-label="Restore"
                  disabled={restoringId === v.id}
                  onClick={() => handleRestore(v.id)}
                  className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 whitespace-nowrap"
                >
                  {restoringId === v.id ? 'Restoring…' : 'Restore'}
                </button>
              </div>
              <div className="flex items-center gap-2">
                {v.version_type && (
                  <span
                    className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${
                      TYPE_BADGE[v.version_type] ?? 'bg-gray-100 text-gray-500'
                    }`}
                  >
                    {TYPE_LABEL[v.version_type] ?? v.version_type}
                  </span>
                )}
                <span className="text-xs text-gray-400">
                  {formatRelative(v.created_at)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- src/components/canvas/VersionHistoryDrawer.test.tsx
```

Expected: 2 PASS.

- [ ] **Step 5: Run the full frontend suite**

```bash
cd frontend && npm test 2>&1 | tail -5
```

Expected: 0 failures (26 total: 24 baseline + 2 new).

- [ ] **Step 6: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 7: Commit**

```bash
git add \
  frontend/src/components/canvas/VersionHistoryDrawer.tsx \
  frontend/src/components/canvas/VersionHistoryDrawer.test.tsx
git commit -m "feat(sprint9a): VersionHistoryDrawer component with restore"
```

---

### Task 4: Frontend — Wire History button into Project page

**Files:**
- Modify: `frontend/src/pages/Project/index.tsx`

- [ ] **Step 1: Add `historyOpen` state and import**

In `frontend/src/pages/Project/index.tsx`:

a. Add the import at the top (after the existing canvas component imports):

```tsx
import { VersionHistoryDrawer } from '../../components/canvas/VersionHistoryDrawer'
```

b. Add state next to the other state declarations (after `hasSavedLayout`):

```tsx
const [historyOpen, setHistoryOpen] = useState(false)
```

- [ ] **Step 2: Add the History button**

In the top-bar button group, add a `History` button. The existing non-editing button group starts at approximately line 283 (the `<>` after `{editing ? ... : (`). Insert the History button **before** the `Save Layout` button cluster. The new block should appear right before the `<div className="flex flex-col items-end">` that contains the version name inputs:

```tsx
<Button variant="secondary" onClick={() => setHistoryOpen(true)}>
  History
</Button>
```

Full updated non-editing button group (replace the `<>...</>` block that currently contains Save Layout / Duplicate / Edit / Delete):

```tsx
<>
  <Button variant="secondary" onClick={() => setHistoryOpen(true)}>
    History
  </Button>
  <div className="flex flex-col items-end">
    <div className="mb-2 grid w-64 gap-1">
      <input
        type="text"
        value={versionName}
        onChange={(e) => setVersionName(e.target.value)}
        placeholder="Version name (optional)"
        className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
      <input
        type="text"
        value={changeSummary}
        onChange={(e) => setChangeSummary(e.target.value)}
        placeholder="Change summary (optional)"
        className="h-8 rounded border border-gray-300 px-2 text-xs focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
    </div>
    <Button
      variant="secondary"
      onClick={handleSaveLayout}
      loading={layoutSaving}
      disabled={!designId || layoutSaving}
    >
      Save Layout
    </Button>
    {layoutSaveError && <p className="text-sm text-red-600 mt-1">{layoutSaveError}</p>}
  </div>
  <div className="flex flex-col items-end">
    <Button variant="secondary" onClick={handleDuplicate} loading={duplicating} disabled={duplicating}>
      Duplicate
    </Button>
    {duplicateError && <p className="text-sm text-red-600 mt-1">{duplicateError}</p>}
  </div>
  <Button variant="secondary" onClick={enterEditMode}>
    Edit
  </Button>
  <div className="flex flex-col items-end">
    <Button
      variant="secondary"
      onClick={handleDelete}
      loading={deleting}
      className="text-red-600 border-red-300 hover:bg-red-50"
    >
      Delete
    </Button>
    {deleteError && <p className="text-sm text-red-600 mt-1">{deleteError}</p>}
  </div>
</>
```

- [ ] **Step 3: Mount the drawer**

Before the final `</div>` that closes the outer `<div className="flex h-screen bg-gray-50">`, mount the drawer:

```tsx
      <VersionHistoryDrawer
        projectId={id!}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />
    </div>
  )
}
```

The complete bottom of the JSX return should look like:

```tsx
        {/* Canvas + Inspector + Prompt bar */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Canvas + Inspector row */}
          <div className="flex-1 flex overflow-hidden">
            <div className="relative flex-1 h-full">
              <Canvas3D className="h-full" />
              <EditorToolbar />
              {!hasSavedLayout && roomCount === 0 && (
                <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                  <div className="rounded border border-dashed border-gray-300 bg-white/90 px-4 py-3 text-sm text-gray-500 shadow-sm">
                    No saved layout yet. Generate a layout from the prompt below.
                  </div>
                </div>
              )}
            </div>
            <Inspector />
          </div>

          {/* Prompt bar */}
          <div className="border-t border-gray-200 bg-white p-3 flex flex-col gap-1">
            <div className="flex gap-2 items-end">
              <textarea
                aria-label="Layout prompt"
                className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
                rows={2}
                placeholder="Describe your layout… e.g. 3 bedroom apartment with open kitchen and living room"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={generating}
              />
              <button
                aria-busy={generating}
                className="bg-indigo-500 hover:bg-indigo-600 disabled:bg-indigo-300 text-white font-medium px-4 py-2 rounded-lg text-sm self-stretch"
                onClick={handleGenerate}
                disabled={generating || !prompt.trim()}
              >
                {generating ? 'Generating…' : 'Generate'}
              </button>
            </div>
            {generateError && (
              <p className="text-xs text-red-500">{generateError}</p>
            )}
          </div>
        </div>
      </main>

      <VersionHistoryDrawer
        projectId={id!}
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
      />
    </div>
  )
}
```

- [ ] **Step 4: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Run the full frontend suite**

```bash
cd frontend && npm test 2>&1 | tail -5
```

Expected: 0 failures (26 total — Task 3 tests still pass after this wiring).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Project/index.tsx
git commit -m "feat(sprint9a): add History button and VersionHistoryDrawer to Project page"
```

---

### Task 5: Update CLAUDE.md + final verification

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update Sprint 9A in CLAUDE.md**

Find the line `### Sprint 9 — Team Collaboration, Version Control, and Logging ⏳ Not Started` and replace it with:

```markdown
### Sprint 9A — Version History & Restore ✅ Complete

- [x] `GET /api/design/version/{version_id}` — fetches a single DesignVersion; 401 / 403 / 404 guarded
- [x] `designId` / `designVersionId` keys stripped from `layout_json` before spread to avoid kwarg collision
- [x] 3 new backend tests (correct layout returned, 403 wrong user, 404 missing)
- [x] `fetchVersion(versionId)` exported from `design.service.ts`
- [x] `VersionHistoryDrawer` component — overlay drawer with version list, type badges, relative timestamps, per-row Restore
- [x] Restore loads the historical layout into the canvas as unsaved changes (user must Save to persist)
- [x] Per-row loading state — only the clicked Restore button shows "Restoring…"
- [x] 2 RTL tests for VersionHistoryDrawer (renders rows, Restore calls API + closes drawer)
- [x] "History" button in project top bar opens the drawer
- [x] `npx tsc --noEmit` passes with zero errors

### Sprint 9B — Activity Log Panel ⏳ Not Started
### Sprint 9C — Auto-save with Drafts ⏳ Not Started
### Sprint 9D — Team Collaboration (Workspaces) ⏳ Not Started
### Sprint 10 — Web Scraper and Data Pipeline ⏳ Not Started
```

- [ ] **Step 2: Run all backend tests one final time**

```bash
cd backend && pytest -q 2>&1 | tail -5
```

Expected: 0 failures.

- [ ] **Step 3: Run all frontend tests one final time**

```bash
cd frontend && npm test 2>&1 | tail -5
```

Expected: 26 PASS.

- [ ] **Step 4: TypeScript final check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Commit and push**

```bash
git add CLAUDE.md
git commit -m "docs(sprint9a): mark Sprint 9A complete in CLAUDE.md"
git push -u origin sprint-9a/version-history
```

Then open a PR: `sprint-9a/version-history` → `main`.

---

## Definition of Done

- [ ] All 5 tasks complete
- [ ] Backend: 87+ tests passing, 0 failures
- [ ] Frontend: 26 tests passing, 0 failures
- [ ] `npx tsc --noEmit` clean
- [ ] `docker-compose up` — History button opens the drawer, versions listed, Restore loads the layout, canvas shows unsaved state
- [ ] PR open on GitHub
