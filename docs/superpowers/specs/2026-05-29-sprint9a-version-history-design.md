# Sprint 9A — Version History & Restore: Design Spec

**Date:** 2026-05-29
**Status:** Approved
**Sprint Goal:** Users can open a version history drawer from the Project page, see all saved versions with name / type / date, and restore any version into the canvas as unsaved changes to review before committing.

---

## Context

Sprint 9 as described in `docs/PROJECT_STRATEGY.md` bundles four independent subsystems (workspaces/teams, version history, activity log, auto-save). This spec covers **Sprint 9A — version history + restore only**. The remaining subsystems will be specced and implemented in separate sub-sprints (9B, 9C, 9D).

### What already exists

| Asset | Introduced in |
|---|---|
| `DesignVersion` SQLAlchemy model with `id`, `design_id`, `project_id`, `user_id`, `version_number`, `version_name`, `version_type`, `change_summary`, `layout_json`, `prompt_used`, `created_at` | Sprint 6 + Sprint 7 (Alembic 004 + 005) |
| `GET /api/projects/{project_id}/versions` → `list[ProjectVersionOut]` (metadata only, no `layout_json`) | Sprint 7 |
| `projectService.versions(id)` in `frontend/src/services/project.service.ts` | Sprint 7 |
| `canvasStore.loadLayout(layout)` — accepts `GenerateResponse`-shaped object | Sprint 6 |
| `GenerateResponse` Pydantic schema + TypeScript interface | Sprint 6 |
| Version history entries created on: generate, manual save, refine, duplicate | Sprints 6–8 |

---

## Scope

### In scope

- `GET /api/design/version/{version_id}` — new endpoint; fetches one `DesignVersion` by ID, returns its `layout_json` as a `GenerateResponse`; validates ownership via the parent `Design`
- `fetchVersion(versionId)` — new function in `frontend/src/services/design.service.ts`
- `VersionHistoryDrawer` — new component at `frontend/src/components/canvas/VersionHistoryDrawer.tsx`; overlay drawer, opens from a "History" button in the project top bar
- Version list — version name, type badge (generated / manual / refined / duplicate), relative timestamp, per-row Restore button
- Restore flow — `fetchVersion(id)` → `canvasStore.loadLayout(result)` → close drawer → canvas shows the restored layout as unsaved changes
- "History" button added to the project top bar
- Backend tests: endpoint returns correct layout, 403 for wrong user, 404 for missing version
- Frontend tests: drawer renders rows, Restore dispatches the correct API call and closes the drawer

### Out of scope

- Auto-save as a new version on Restore (restore is load-only; user must click Save Layout to persist) — intentional
- Canvas preview of a version before applying it — Sprint 9A+
- Rename or delete a version — not specced
- Activity log panel — Sprint 9B
- Auto-save with drafts — Sprint 9C
- Workspaces and team collaboration — Sprint 9D

---

## Architecture

### Backend flow

```text
GET /api/design/version/{version_id}
  → load DesignVersion by id (404 "Version not found" if missing)
  → load parent Design (to get user_id)
  → if design.user_id != current_user_id → 403 "Access forbidden"
  → return GenerateResponse(**version.layout_json,
                            designId=design.id,
                            designVersionId=version.id)
```

No new schema is needed — `GenerateResponse` already covers the full layout shape.

### Frontend flow

```text
User clicks "History" button in top bar
  → historyOpen = true
  → VersionHistoryDrawer mounts, calls projectService.versions(projectId)
  → Loading spinner while fetching
  → Renders version list newest-first
      Each row: version_name | type badge | relative timestamp | [Restore]

User clicks Restore on a row
  → row's restoringId = version.id (per-row loading, others stay enabled)
  → fetchVersion(version.id) → GET /api/design/version/{version_id}
  → canvasStore.loadLayout(result)
  → historyOpen = false (drawer closes)
  → canvas shows restored layout; saveStatus = 'unsaved'
  → user must click Save Layout to persist as a new version
```

---

## File Map

```text
backend/app/
├── api/designs/router.py          MODIFY — add GET /version/{version_id}
└── tests/test_designs.py          MODIFY — 3 new version-fetch tests

frontend/src/
├── components/canvas/
│   └── VersionHistoryDrawer.tsx   CREATE
├── services/
│   └── design.service.ts          MODIFY — add fetchVersion
└── pages/Project/
    ├── index.tsx                   MODIFY — History button + VersionHistoryDrawer mount
    └── index.test.tsx              MODIFY — 2 new drawer tests
```

---

## Backend: `GET /api/design/version/{version_id}`

Added to `backend/app/api/designs/router.py`, registered with the existing `router = APIRouter(prefix="/api/design")`.

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

    layout = {k: v for k, v in version.layout_json.items() if k not in ("designId", "designVersionId")}
    return GenerateResponse(
        **layout,
        designId=design.id,
        designVersionId=version.id,
    )
```

Note: `design` is loaded to validate ownership. If the `Design` row was deleted (orphaned version), 403 is returned — this is a safe failure mode.

### Error table

| Scenario | Status | Detail |
|---|---|---|
| Missing Bearer token | 401 | `Not authenticated` |
| Version ID does not exist | 404 | `Version not found` |
| Parent design belongs to another user | 403 | `Access forbidden` |

### Backend tests (added to `test_designs.py`)

```python
async def test_fetch_version_returns_correct_layout(client, token, project_id):
    # generate → fetch the generated version ID → GET /api/design/version/{id}
    # assert 200, rooms match original generation, designVersionId correct

async def test_fetch_version_wrong_user_returns_403(client):
    # token_a generates design, token_b tries to fetch its version → 403

async def test_fetch_version_not_found_returns_404(client, token):
    # GET /api/design/version/nonexistent-id → 404
```

---

## Frontend: `design.service.ts`

Append one function:

```typescript
export async function fetchVersion(versionId: string): Promise<GenerateResponse> {
  const { data } = await api.get<GenerateResponse>(`/api/design/version/${versionId}`)
  return data
}
```

---

## Frontend: `VersionHistoryDrawer.tsx`

New file at `frontend/src/components/canvas/VersionHistoryDrawer.tsx`.

### Props

```typescript
interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}
```

### State

```typescript
const [versions, setVersions] = useState<ProjectVersion[]>([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
const [restoringId, setRestoringId] = useState<string | null>(null)
const loadLayout = useCanvasStore((s) => s.loadLayout)
```

### Data fetch

```typescript
useEffect(() => {
  if (!open) return
  setLoading(true)
  setError(null)
  projectService.versions(projectId)
    .then(setVersions)
    .catch(() => setError('Failed to load version history.'))
    .finally(() => setLoading(false))
}, [open, projectId])
```

### Restore handler

```typescript
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
```

### Type badge colours

| `version_type` | Label | Tailwind colour |
|---|---|---|
| `generated` | Generated | `bg-indigo-100 text-indigo-700` |
| `manual` | Manual save | `bg-emerald-100 text-emerald-700` |
| `refined` | Refined | `bg-amber-100 text-amber-700` |
| `duplicate` | Duplicate | `bg-gray-100 text-gray-600` |
| (other / null) | — | `bg-gray-100 text-gray-500` |

### Timestamp helper

```typescript
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
```

### Layout

```tsx
{open && (
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
              disabled={restoringId === v.id}
              onClick={() => handleRestore(v.id)}
              className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 whitespace-nowrap"
            >
              {restoringId === v.id ? 'Restoring…' : 'Restore'}
            </button>
          </div>
          <div className="flex items-center gap-2">
            {v.version_type && (
              <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded ${TYPE_BADGE[v.version_type] ?? TYPE_BADGE.default}`}>
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
)}
```

Backdrop: a transparent overlay that calls `onClose()` when clicked, placed behind the drawer panel.

---

## Frontend: `pages/Project/index.tsx` changes

### State addition

```typescript
const [historyOpen, setHistoryOpen] = useState(false)
```

### Top-bar button (added alongside existing buttons)

```tsx
<Button variant="secondary" onClick={() => setHistoryOpen(true)}>
  History
</Button>
```

### Drawer mount (before the closing `</div>` of the page root)

```tsx
<VersionHistoryDrawer
  projectId={id!}
  open={historyOpen}
  onClose={() => setHistoryOpen(false)}
/>
```

---

## Frontend: Tests

### `VersionHistoryDrawer.test.tsx` (new — 2 tests)

Both tests mock `api.get` and `projectService.versions`.

**Test 1: renders version rows when open**
```typescript
// mock projectService.versions to return 2 version fixtures
// render <VersionHistoryDrawer projectId="p1" open={true} onClose={vi.fn()} />
// assert both version names appear in the document
// assert Restore buttons are present (one per row)
```

**Test 2: Restore calls fetchVersion and closes the drawer**
```typescript
// mock api.get to return a designFixture for /api/design/version/v1
// click the first Restore button
// await waitFor: api.get called with /api/design/version/v1
// assert onClose was called
```

### `pages/Project/index.test.tsx` additions (2 tests)

**Test 3: History button opens the drawer**
```typescript
// render project page with a loaded design
// click "History" button
// assert role="dialog" is present in the document
```

**Test 4: Closing the drawer removes it**
```typescript
// open the drawer via History button
// click the close button (aria-label="Close history")
// assert role="dialog" is no longer in the document
```

---

## Definition of Done

- [ ] `GET /api/design/version/{version_id}` registered and guarded (401/403/404)
- [ ] 3 new backend tests (fetch correct layout, wrong-user 403, missing 404)
- [ ] `fetchVersion` exported from `design.service.ts`
- [ ] `VersionHistoryDrawer` renders version rows with name, type badge, relative timestamp, Restore button
- [ ] Restore fetches the version, loads it into the canvas, closes the drawer
- [ ] Per-row loading state — only the clicked row's button shows "Restoring…"
- [ ] Empty state, loading state, and error state rendered in the drawer
- [ ] "History" button in project top bar opens the drawer
- [ ] All existing backend tests still pass
- [ ] All existing frontend tests still pass + 4 new tests green
- [ ] `npx tsc --noEmit` clean
- [ ] `docker-compose up` — History button opens the drawer, Restore loads the version
