# Sprint 9B — Activity Log Panel: Design Spec

**Date:** 2026-05-29
**Status:** Approved
**Sprint Goal:** Users can open an Activity drawer from the Project page and see the last 50 actions taken on this project (created, updated, generated, saved, refined, duplicated), each labeled with a human-friendly description and a relative timestamp.

---

## Context

Sprint 9 was decomposed into 9A/9B/9C/9D during brainstorming. This spec covers Sprint 9B — the activity feed UI. The other sub-sprints (auto-save, workspaces) will be specced separately.

### What already exists

| Asset | Introduced |
|---|---|
| `ActivityLog(id, user_id, action, timestamp)` model — minimal schema | Sprint 2 |
| `Alembic 003_create_activity_logs.py` | Sprint 2 |
| `log_activity(db, user_id, action)` helper in `backend/app/utils/activity.py` | Sprint 2 |
| 8 `log_activity` call sites across `project_service.py` and `designs/router.py` (`project.created`, `project.updated`, `project.deleted`, `project.duplicated`, `design.generated`, `layout.saved`, `design.refined`) | Sprints 2, 6, 7, 8 |
| `VersionHistoryDrawer` overlay drawer pattern (`backdrop + drawer + header + list`) | Sprint 9A |
| `formatRelative(iso)` helper inside `VersionHistoryDrawer.tsx` | Sprint 9A |
| `Button` UI component, `useCanvasStore`, `projectService.versions()` | Sprints 1, 6, 7 |

### The core constraint

The current `ActivityLog` table has **no `project_id` column**. The 8 existing call sites log only an action string. To scope activity per project, a small schema change is required as part of this sprint. This is the spec's most important architectural decision.

---

## Scope

### In scope

- Alembic migration `006_add_activity_project_id.py` — add `project_id: str | None` column to `activity_logs` (nullable, indexed, **no FK constraint** — see "Why no FK" below). No backfill — existing rows keep `project_id = NULL`.
- Update `ActivityLog` SQLAlchemy model with the new column
- Extend `log_activity(db, user_id, action, project_id=None)` — new keyword-only param defaults to `None` for backward compatibility
- Update all 8 existing `log_activity` call sites to pass the relevant `project_id`
- New endpoint `GET /api/projects/{project_id}/activity` returning the 50 newest rows for that project, newest-first; owned-project check (403/404)
- New `ActivityLogOut` Pydantic schema
- New `list_project_activity(db, user_id, project_id)` service function in `project_service.py`
- Frontend: `projectService.activity(id)` and `ActivityEntry` interface in `project.service.ts`
- New `ActivityDrawer` component at `frontend/src/components/canvas/ActivityDrawer.tsx` (mirrors `VersionHistoryDrawer` structure)
- Human-friendly action label mapping (`ACTION_LABEL` constant)
- `formatRelative` helper extracted from `VersionHistoryDrawer.tsx` to `frontend/src/utils/time.ts`; both drawers import from there
- "Activity" button placed next to the existing "History" button in the project top bar
- Backend tests: scoped + ordered, 403 wrong user, isolation between projects (3 tests)
- Frontend tests: `ActivityDrawer.test.tsx` (2 RTL tests) + 1 new Project page test for the Activity button

### Out of scope

- A `metadata` JSON column on `ActivityLog` (deferred — no UI surface for it yet)
- Old/new value diffs in rows (deferred)
- User name display per row (single-user product until Sprint 9D adds workspaces)
- Restore actions from the activity feed (the version history drawer is the canonical restore path)
- Pagination, cursor, "Load older" button — only the 50 newest are returned
- Server-side filtering or search
- Backfilling `project_id` into historical rows (NULL forever for them)

---

## Architecture

### Backend flow

```text
GET /api/projects/{project_id}/activity
  → _current_user_id (401 if missing token)
  → list_project_activity(db, user_id, project_id):
      ├── _get_owned_project (404 or 403)
      └── SELECT * FROM activity_logs
            WHERE project_id = ?
            ORDER BY timestamp DESC
            LIMIT 50
  → 200 list[ActivityLogOut]
```

### Write path (after Sprint 9B)

Every existing `log_activity(db, user_id, action)` becomes `log_activity(db, user_id, action, project_id=<id>)`. Compatibility: the new param defaults to `None`, so external code paths that don't know about projects still work.

### Frontend flow

```text
User clicks "Activity" button in top bar
  → activityOpen = true
  → ActivityDrawer mounts
  → projectService.activity(projectId) → GET /api/projects/{id}/activity
  → Loading spinner
  → Renders rows newest-first
      Each row: labelFor(action) | formatRelative(timestamp)
User clicks close (or backdrop)
  → activityOpen = false
  → drawer unmounts
```

---

## File Map

```text
backend/
├── alembic/versions/
│   └── 006_add_activity_project_id.py   CREATE
├── app/
│   ├── models/activity_log.py            MODIFY — add project_id column
│   ├── utils/activity.py                 MODIFY — log_activity gains project_id kwarg
│   ├── services/project_service.py       MODIFY — list_project_activity + update 4 call sites
│   ├── api/projects/router.py            MODIFY — GET /activity endpoint
│   ├── api/designs/router.py             MODIFY — pass project_id in 3 log_activity calls
│   ├── schemas/project.py                MODIFY — ActivityLogOut
│   └── tests/
│       └── test_projects.py              MODIFY — 3 new activity tests

frontend/src/
├── utils/
│   └── time.ts                            CREATE — formatRelative
├── components/canvas/
│   ├── VersionHistoryDrawer.tsx           MODIFY — import formatRelative from utils
│   ├── ActivityDrawer.tsx                 CREATE
│   └── ActivityDrawer.test.tsx            CREATE — 2 RTL tests
├── services/
│   └── project.service.ts                 MODIFY — add ActivityEntry + activity() method
└── pages/Project/
    ├── index.tsx                           MODIFY — activityOpen state, button, drawer mount
    └── index.test.tsx                      MODIFY — 1 new test
```

---

## Backend: Alembic `006_add_activity_project_id.py`

```python
"""add project_id to activity_logs

Revision ID: 006
Revises: 005
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("activity_logs", sa.Column("project_id", sa.String(), nullable=True))
    op.create_index(
        "ix_activity_logs_project_id",
        "activity_logs",
        ["project_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_logs_project_id", table_name="activity_logs")
    op.drop_column("activity_logs", "project_id")
```

### Why no FK constraint

`project.deleted` is logged *after* the row is removed (in `delete_project`). If `activity_logs.project_id` had an FK to `projects.id`, the insert would fail. Two ways to fix:
1. Log `project.deleted` *before* the delete (small refactor, fragile).
2. Drop the FK — activity logs are append-only audit trail and should outlive the entities they reference.

Option 2 is correct: a deleted project's history should remain visible in any global audit view, and an indexed string column is just as fast for lookups as an FK-backed one.

---

## Backend: `ActivityLog` model

```python
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

---

## Backend: `log_activity` helper

```python
async def log_activity(
    db: AsyncSession,
    user_id: str,
    action: str,
    project_id: str | None = None,
) -> None:
    try:
        entry = ActivityLog(user_id=user_id, action=action, project_id=project_id)
        db.add(entry)
        await db.commit()
    except Exception as exc:
        print(f"[activity log error] {exc}", file=sys.stderr)
```

---

## Backend: Call site updates

Every existing `log_activity(db, user_id, action)` is updated to pass `project_id`. Mapping:

| Location | Action | project_id source |
|---|---|---|
| `project_service.create_project` | `project.created` | `project.id` (the newly created row) |
| `project_service.update_project` | `project.updated` | `project_id` (function parameter) |
| `project_service.delete_project` | `project.deleted` | `project_id` (still passed even though the row is gone — no FK to break) |
| `project_service.duplicate_project` | `project.duplicated` | `duplicate.id` (the new copy's ID) |
| `designs/router.generate` | `design.generated` | `request.project_id` if non-None (skip the kwarg when generating without a project) |
| `designs/router.save_design` | `layout.saved` | `design.project_id` |
| `designs/router.refine` | `design.refined` | `design.project_id` |

For `designs/router.generate`: only pass `project_id` when `request.project_id` is set, since some generations are project-less.

---

## Backend: `ActivityLogOut` schema

In `backend/app/schemas/project.py` (alongside `ProjectVersionOut`):

```python
class ActivityLogOut(BaseModel):
    id: str
    action: str
    timestamp: datetime

    model_config = {"from_attributes": True}
```

---

## Backend: `list_project_activity` service function

In `backend/app/services/project_service.py` (alongside `list_project_versions`):

```python
async def list_project_activity(
    db: AsyncSession, user_id: str, project_id: str
) -> list[ActivityLogOut]:
    await _get_owned_project(db, user_id, project_id)
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .order_by(desc(ActivityLog.timestamp))
        .limit(50)
    )
    entries = result.scalars().all()
    return [ActivityLogOut.model_validate(e) for e in entries]
```

---

## Backend: `GET /api/projects/{project_id}/activity` endpoint

In `backend/app/api/projects/router.py`, alongside the existing `versions` endpoint:

```python
@router.get("/{project_id}/activity", response_model=list[ActivityLogOut])
async def activity(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_project_activity(db, user_id, project_id)
```

### Error responses

| Scenario | Status | Detail |
|---|---|---|
| Missing Bearer token | 401 | `Not authenticated` |
| Project does not exist | 404 | `Project not found` |
| Project owned by another user | 403 | `Access forbidden` |

---

## Backend: Tests (3 new in `test_projects.py`)

### `test_project_activity_returns_scoped_entries_newest_first`

```python
async def test_project_activity_returns_scoped_entries_newest_first(client: AsyncClient):
    # 1. register, create project (logs project.created)
    # 2. POST /api/design/generate with projectId (logs design.generated)
    # 3. PUT /api/design/{id} (logs layout.saved)
    # 4. GET /api/projects/{id}/activity
    # 5. assert response is exactly 3 entries, ordered ["layout.saved", "design.generated", "project.created"]
```

### `test_project_activity_wrong_user_returns_403`

Token A creates a project, token B requests `/activity` → 403.

### `test_project_activity_only_includes_this_project`

Create two projects A and B. Generate on A, generate on B, save on A. Fetch `/activity` for A → assert it contains exactly A's entries; fetch for B → assert it contains exactly B's entries. No bleed-over.

---

## Frontend: `frontend/src/utils/time.ts` (extracted)

```typescript
export function formatRelative(iso: string): string {
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

Update `VersionHistoryDrawer.tsx` to `import { formatRelative } from '../../utils/time'` and remove the local copy.

---

## Frontend: `project.service.ts` additions

```typescript
export interface ActivityEntry {
  id: string
  action: string
  timestamp: string
}

const projectService = {
  // ... existing methods
  activity: (id: string): Promise<ActivityEntry[]> =>
    api.get(`/api/projects/${id}/activity`).then((r) => r.data),
}
```

---

## Frontend: `ActivityDrawer.tsx`

New file at `frontend/src/components/canvas/ActivityDrawer.tsx`. Same structural pattern as `VersionHistoryDrawer`.

### Props and state

```typescript
interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

const [entries, setEntries] = useState<ActivityEntry[]>([])
const [loading, setLoading] = useState(false)
const [error, setError] = useState<string | null>(null)
const isMounted = useRef(true)
```

### Mount/unmount cleanup

```typescript
useEffect(() => {
  isMounted.current = true
  return () => {
    isMounted.current = false
  }
}, [])
```

### Data fetch

```typescript
useEffect(() => {
  if (!open) return
  setLoading(true)
  setError(null)
  projectService
    .activity(projectId)
    .then((data) => {
      if (isMounted.current) setEntries(data)
    })
    .catch(() => {
      if (isMounted.current) setError('Failed to load activity.')
    })
    .finally(() => {
      if (isMounted.current) setLoading(false)
    })
}, [open, projectId])
```

### Action label map

```typescript
const ACTION_LABEL: Record<string, string> = {
  'project.created': 'Created project',
  'project.updated': 'Updated project',
  'project.deleted': 'Deleted project',
  'project.duplicated': 'Duplicated project',
  'design.generated': 'Generated layout',
  'design.refined': 'Refined layout',
  'layout.saved': 'Saved layout',
}

function labelFor(action: string): string {
  return ACTION_LABEL[action] ?? action
}
```

### Layout

```tsx
if (!open) return null

return (
  <>
    <div
      className="fixed inset-0 z-40"
      aria-hidden="true"
      onClick={onClose}
    />
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Project activity"
      className="fixed inset-y-0 right-0 z-50 w-80 bg-white shadow-xl flex flex-col"
    >
      <div className="flex items-center justify-between border-b border-gray-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-gray-900">Activity</h2>
        <button
          type="button"
          aria-label="Close activity"
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2">
        {loading && <p className="text-sm text-gray-400">Loading…</p>}
        {error && <p className="text-sm text-red-500">{error}</p>}
        {!loading && !error && entries.length === 0 && (
          <p className="text-sm text-gray-400">No activity yet.</p>
        )}
        {entries.map((e) => (
          <div
            key={e.id}
            className="rounded border border-gray-200 p-3 flex flex-col gap-0.5"
          >
            <span className="text-sm font-medium text-gray-800">
              {labelFor(e.action)}
            </span>
            <span className="text-xs text-gray-400">
              {formatRelative(e.timestamp)}
            </span>
          </div>
        ))}
      </div>
    </div>
  </>
)
```

---

## Frontend: `pages/Project/index.tsx` changes

```typescript
// imports
import { ActivityDrawer } from '../../components/canvas/ActivityDrawer'

// state (next to historyOpen)
const [activityOpen, setActivityOpen] = useState(false)

// top-bar button (next to the existing History button)
<Button variant="secondary" onClick={() => setActivityOpen(true)}>
  Activity
</Button>

// drawer mount (next to VersionHistoryDrawer)
<ActivityDrawer
  projectId={id!}
  open={activityOpen}
  onClose={() => setActivityOpen(false)}
/>
```

---

## Frontend: Tests

### `ActivityDrawer.test.tsx` (2 new)

**Test 1: renders rows with human-friendly labels**
```typescript
// mock projectService.activity to return [
//   { id: 'a1', action: 'layout.saved', timestamp: '...' },
//   { id: 'a2', action: 'design.generated', timestamp: '...' },
// ]
// render <ActivityDrawer projectId="p1" open={true} onClose={vi.fn()} />
// assert 'Saved layout' and 'Generated layout' both appear
```

**Test 2: renders empty state when API returns []**
```typescript
// mock projectService.activity to resolve to []
// render the drawer
// assert text 'No activity yet.' is in the document
```

### `pages/Project/index.test.tsx` additions (1 new)

**Test: Activity button opens the drawer**
```typescript
// renderProjectPage()
// click button name 'Activity'
// assert role 'dialog' with aria-label 'Project activity' is in the document
```

---

## Definition of Done

- [ ] Alembic `006` adds `project_id` to `activity_logs` (nullable, indexed, no FK)
- [ ] `ActivityLog.project_id` declared on the SQLAlchemy model
- [ ] `log_activity` accepts `project_id` (default `None`); all 7 existing call sites updated
- [ ] `GET /api/projects/{project_id}/activity` returns 50 newest rows, scoped to the project, 401/403/404 guarded
- [ ] `ActivityLogOut` schema added
- [ ] 3 backend tests passing (scoped + ordered, wrong user, isolation between projects)
- [ ] `formatRelative` moved to `frontend/src/utils/time.ts`; both drawers import it
- [ ] `projectService.activity()` and `ActivityEntry` exported
- [ ] `ActivityDrawer` mirrors the version drawer's structure (backdrop + drawer, `role="dialog"`, `aria-modal="true"`, `aria-label="Project activity"`)
- [ ] `ActivityDrawer` action label map covers all 7 known action strings; unknown actions render the raw string
- [ ] `isMounted` ref guards setState calls against unmount
- [ ] "Activity" button in project top bar next to "History"
- [ ] 2 `ActivityDrawer.test.tsx` tests passing
- [ ] 1 new `Project/index.test.tsx` test passing
- [ ] All existing tests still green
- [ ] `npx tsc --noEmit` clean
- [ ] `docker-compose up` — Activity button opens the drawer, latest actions render correctly
