# Sprint 9B — Activity Log Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users open an Activity drawer from the Project page and see the latest 50 actions taken on this project, each labeled with a human-friendly description and a relative timestamp.

**Architecture:** Alembic migration `006` adds a nullable, indexed `project_id` column to `activity_logs` (no FK — append-only audit data must survive project deletes). The `log_activity` helper gains a `project_id` kwarg, and all 7 existing call sites pass the relevant ID. A new `GET /api/projects/{project_id}/activity` endpoint returns the 50 newest rows scoped to one project. The frontend mirrors the Sprint 9A `VersionHistoryDrawer` pattern in a new `ActivityDrawer` component, with `formatRelative` extracted into a shared `utils/time.ts` so both drawers stay in sync.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Pydantic v2, pytest, React 18, TypeScript, Zustand, Vitest, React Testing Library, happy-dom.

**Spec:** [docs/superpowers/specs/2026-05-29-sprint9b-activity-log-design.md](../specs/2026-05-29-sprint9b-activity-log-design.md)

**Branch:** `sprint-9b/activity-log` (already created off `sprint-9a/version-history`)

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `backend/alembic/versions/006_add_activity_project_id.py` | CREATE | Add `project_id` column + index |
| `backend/app/models/activity_log.py` | MODIFY | Add `project_id` field |
| `backend/app/utils/activity.py` | MODIFY | `log_activity` accepts `project_id` kwarg |
| `backend/app/services/project_service.py` | MODIFY | 4 call-site updates + `list_project_activity` |
| `backend/app/api/projects/router.py` | MODIFY | `GET /{project_id}/activity` endpoint |
| `backend/app/api/designs/router.py` | MODIFY | 3 call-site updates (generate, save, refine) |
| `backend/app/schemas/project.py` | MODIFY | `ActivityLogOut` schema |
| `backend/app/tests/test_projects.py` | MODIFY | 3 new activity endpoint tests |
| `frontend/src/utils/time.ts` | CREATE | `formatRelative` helper |
| `frontend/src/components/canvas/VersionHistoryDrawer.tsx` | MODIFY | Import `formatRelative` from utils, drop local copy |
| `frontend/src/services/project.service.ts` | MODIFY | `ActivityEntry` + `activity()` method |
| `frontend/src/components/canvas/ActivityDrawer.tsx` | CREATE | Drawer component |
| `frontend/src/components/canvas/ActivityDrawer.test.tsx` | CREATE | 2 RTL tests |
| `frontend/src/pages/Project/index.tsx` | MODIFY | Activity button + drawer mount |
| `frontend/src/pages/Project/index.test.tsx` | MODIFY | 1 new test |
| `CLAUDE.md` | MODIFY | Mark Sprint 9B complete |

---

## Pre-flight

```bash
git branch --show-current   # expected: sprint-9b/activity-log
git log --oneline -3        # expected: spec commit on top
```

Verify baseline:

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest -q 2>&1 | tail -3
# expected: 87 passed (Sprint 9A baseline)
cd frontend && npm test 2>&1 | tail -3
# expected: 31 passed
```

If anything is red, stop and fix before starting.

---

### Task 1: Alembic migration `006_add_activity_project_id.py`

**Files:**
- Create: `backend/alembic/versions/006_add_activity_project_id.py`

- [ ] **Step 1: Verify the previous revision id**

```bash
grep -l "down_revision" backend/alembic/versions/005_*.py
grep "revision = " backend/alembic/versions/005_*.py
```

Expected: `revision = "005"` — confirms the new migration's `down_revision = "005"`.

- [ ] **Step 2: Create the migration**

Create `backend/alembic/versions/006_add_activity_project_id.py`:

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

- [ ] **Step 3: Commit**

```bash
git add backend/alembic/versions/006_add_activity_project_id.py
git commit -m "feat(sprint9b): alembic 006 adds project_id to activity_logs"
```

---

### Task 2: Update `ActivityLog` model

**Files:**
- Modify: `backend/app/models/activity_log.py`

- [ ] **Step 1: Add the `project_id` field**

Replace the contents of `backend/app/models/activity_log.py`:

```python
import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


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

- [ ] **Step 2: Verify SQLAlchemy still imports cleanly**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key python -c "from app.models.activity_log import ActivityLog; print(ActivityLog.__table__.columns.keys())"
```

Expected output: `['id', 'user_id', 'project_id', 'action', 'timestamp']`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/activity_log.py
git commit -m "feat(sprint9b): ActivityLog gains project_id column"
```

---

### Task 3: Extend `log_activity` helper

**Files:**
- Modify: `backend/app/utils/activity.py`

- [ ] **Step 1: Update the helper**

Replace `backend/app/utils/activity.py`:

```python
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(
    db: AsyncSession,
    user_id: str,
    action: str,
    project_id: str | None = None,
) -> None:
    try:
        entry = ActivityLog(
            user_id=user_id, action=action, project_id=project_id
        )
        db.add(entry)
        await db.commit()
    except Exception as exc:
        print(f"[activity log error] {exc}", file=sys.stderr)
```

- [ ] **Step 2: Run baseline backend tests**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest -q 2>&1 | tail -3
```

Expected: 87 passed. (Existing call sites don't pass `project_id` yet — the default keeps backward compatibility.)

- [ ] **Step 3: Commit**

```bash
git add backend/app/utils/activity.py
git commit -m "feat(sprint9b): log_activity accepts project_id kwarg"
```

---

### Task 4: Update `log_activity` call sites in `project_service.py`

**Files:**
- Modify: `backend/app/services/project_service.py`

- [ ] **Step 1: Patch the four call sites**

In `backend/app/services/project_service.py`, update each `log_activity` call to pass `project_id`:

1. `create_project` (around line 32) — change from:
   ```python
   await log_activity(db, user_id, "project.created")
   ```
   to:
   ```python
   await log_activity(db, user_id, "project.created", project_id=project.id)
   ```

2. `update_project` (around line 62) — change to:
   ```python
   await log_activity(db, user_id, "project.updated", project_id=project_id)
   ```

3. `delete_project` (around line 74) — change to:
   ```python
   await log_activity(db, user_id, "project.deleted", project_id=project_id)
   ```

4. `duplicate_project` (around line 147) — change to:
   ```python
   await log_activity(db, user_id, "project.duplicated", project_id=duplicate.id)
   ```

- [ ] **Step 2: Run project tests (existing ones must still pass)**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest app/tests/test_projects.py -v 2>&1 | tail -15
```

Expected: all 11 existing project tests still pass. (They only assert the action string is present, not `project_id`.)

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/project_service.py
git commit -m "feat(sprint9b): project_service log_activity calls include project_id"
```

---

### Task 5: Update `log_activity` call sites in `designs/router.py`

**Files:**
- Modify: `backend/app/api/designs/router.py`

- [ ] **Step 1: Patch the three call sites**

In `backend/app/api/designs/router.py`:

1. `generate` (around line 74) — change from:
   ```python
   await log_activity(db, user_id, "design.generated")
   ```
   to:
   ```python
   await log_activity(
       db, user_id, "design.generated", project_id=request.project_id
   )
   ```
   (`request.project_id` is `None` when generating without a project — `log_activity` handles that.)

2. `save_design` (around line 109) — change to:
   ```python
   await log_activity(db, user_id, "layout.saved", project_id=design.project_id)
   ```

3. `refine` (around line 172) — change to:
   ```python
   await log_activity(db, user_id, "design.refined", project_id=design.project_id)
   ```

- [ ] **Step 2: Run design tests**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest app/tests/test_designs.py -v 2>&1 | tail -15
```

Expected: all existing design tests still pass.

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/designs/router.py
git commit -m "feat(sprint9b): designs router log_activity calls include project_id"
```

---

### Task 6: Add `ActivityLogOut` schema

**Files:**
- Modify: `backend/app/schemas/project.py`

- [ ] **Step 1: Append the new schema**

Append to `backend/app/schemas/project.py` (after the existing `ProjectVersionOut`):

```python
class ActivityLogOut(BaseModel):
    id: str
    action: str
    timestamp: datetime

    model_config = {"from_attributes": True}
```

The existing `from datetime import datetime` and `from pydantic import BaseModel` imports at the top of the file are already present — do not duplicate them.

- [ ] **Step 2: Verify import works**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key python -c "from app.schemas.project import ActivityLogOut; print(ActivityLogOut.model_fields.keys())"
```

Expected output: `dict_keys(['id', 'action', 'timestamp'])`.

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/project.py
git commit -m "feat(sprint9b): add ActivityLogOut schema"
```

---

### Task 7: Backend `list_project_activity` service + endpoint + tests

**Files:**
- Modify: `backend/app/services/project_service.py`
- Modify: `backend/app/api/projects/router.py`
- Modify: `backend/app/tests/test_projects.py`

- [ ] **Step 1: Write the failing tests**

Append to `backend/app/tests/test_projects.py`:

```python
async def test_project_activity_returns_scoped_entries_newest_first(client: AsyncClient):
    token = await _register_and_token(client, "activity@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Activity Project", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = project.json()["id"]

    generated = await client.post(
        "/api/design/generate",
        json={"projectId": project_id, "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )
    design = generated.json()
    await client.put(
        f"/api/design/{design['designId']}",
        json={"layout": design, "versionName": "v"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        f"/api/projects/{project_id}/activity",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    entries = response.json()
    actions = [e["action"] for e in entries]
    assert actions == ["layout.saved", "design.generated", "project.created"]


async def test_project_activity_wrong_user_returns_403(client: AsyncClient):
    token_a = await _register_and_token(client, "activity-owner@example.com")
    token_b = await _register_and_token(client, "activity-intruder@example.com")
    project = await client.post(
        "/api/projects",
        json={"title": "Owned", "description": None},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await client.get(
        f"/api/projects/{project.json()['id']}/activity",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403


async def test_project_activity_isolates_between_projects(client: AsyncClient):
    token = await _register_and_token(client, "activity-iso@example.com")

    project_a = await client.post(
        "/api/projects",
        json={"title": "A", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_b = await client.post(
        "/api/projects",
        json={"title": "B", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/design/generate",
        json={"projectId": project_a.json()["id"], "prompt": "2 bedroom apartment with kitchen"},
        headers={"Authorization": f"Bearer {token}"},
    )

    activity_a = await client.get(
        f"/api/projects/{project_a.json()['id']}/activity",
        headers={"Authorization": f"Bearer {token}"},
    )
    activity_b = await client.get(
        f"/api/projects/{project_b.json()['id']}/activity",
        headers={"Authorization": f"Bearer {token}"},
    )

    actions_a = sorted(e["action"] for e in activity_a.json())
    actions_b = sorted(e["action"] for e in activity_b.json())

    assert actions_a == ["design.generated", "project.created"]
    assert actions_b == ["project.created"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest app/tests/test_projects.py::test_project_activity_returns_scoped_entries_newest_first -v
```

Expected: FAIL — 404 / route not registered.

- [ ] **Step 3: Add `list_project_activity` to the service**

In `backend/app/services/project_service.py`, ensure the top-level imports include:

```python
from app.models.activity_log import ActivityLog
from app.schemas.project import ActivityLogOut, ProjectCreate, ProjectOut, ProjectUpdate, ProjectVersionOut
```

(Merge — do not duplicate. `ProjectCreate, ProjectOut, ProjectUpdate, ProjectVersionOut` are already imported.)

Append the function to `project_service.py` (after `duplicate_project`):

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

- [ ] **Step 4: Add the endpoint**

In `backend/app/api/projects/router.py`, update the imports near the top:

```python
from app.schemas.project import ActivityLogOut, ProjectCreate, ProjectOut, ProjectUpdate, ProjectVersionOut
from app.services.project_service import (
    create_project,
    delete_project,
    duplicate_project,
    get_project,
    list_project_activity,
    list_project_versions,
    list_projects,
    update_project,
)
```

(Merge with existing imports — keep alphabetical order.)

Append the endpoint at the bottom of the file:

```python
@router.get("/{project_id}/activity", response_model=list[ActivityLogOut])
async def activity(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_project_activity(db, user_id, project_id)
```

- [ ] **Step 5: Run all three new tests**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest \
  app/tests/test_projects.py::test_project_activity_returns_scoped_entries_newest_first \
  app/tests/test_projects.py::test_project_activity_wrong_user_returns_403 \
  app/tests/test_projects.py::test_project_activity_isolates_between_projects -v
```

Expected: 3 PASS.

- [ ] **Step 6: Run the full backend suite**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest -q 2>&1 | tail -3
```

Expected: 90 passed (baseline 87 + 3 new).

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/project_service.py backend/app/api/projects/router.py backend/app/tests/test_projects.py
git commit -m "feat(sprint9b): GET /api/projects/{id}/activity endpoint"
```

---

### Task 8: Extract `formatRelative` to shared utility

**Files:**
- Create: `frontend/src/utils/time.ts`
- Modify: `frontend/src/components/canvas/VersionHistoryDrawer.tsx`

- [ ] **Step 1: Create the shared helper**

Create `frontend/src/utils/time.ts`:

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

- [ ] **Step 2: Update `VersionHistoryDrawer.tsx`**

In `frontend/src/components/canvas/VersionHistoryDrawer.tsx`:

a. Remove the local `formatRelative` function definition (lines 26-35 of the existing file).

b. Add the import at the top of the file (after the existing imports):

```typescript
import { formatRelative } from '../../utils/time'
```

- [ ] **Step 3: Verify TypeScript and tests are clean**

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm test 2>&1 | tail -5
```

Expected: zero TS errors. 31 tests passing.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/time.ts frontend/src/components/canvas/VersionHistoryDrawer.tsx
git commit -m "refactor(sprint9b): extract formatRelative to utils/time"
```

---

### Task 9: Frontend `projectService.activity()` + `ActivityEntry` type

**Files:**
- Modify: `frontend/src/services/project.service.ts`

- [ ] **Step 1: Add type and method**

In `frontend/src/services/project.service.ts`, append the `ActivityEntry` interface (after the existing `ProjectVersion` interface):

```typescript
export interface ActivityEntry {
  id: string
  action: string
  timestamp: string
}
```

Inside the `projectService` object, add an `activity` method (alongside the existing `versions` method):

```typescript
  activity: (id: string): Promise<ActivityEntry[]> =>
    api.get(`/api/projects/${id}/activity`).then((r) => r.data),
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/project.service.ts
git commit -m "feat(sprint9b): add projectService.activity"
```

---

### Task 10: `ActivityDrawer` component + tests

**Files:**
- Create: `frontend/src/components/canvas/ActivityDrawer.tsx`
- Create: `frontend/src/components/canvas/ActivityDrawer.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/components/canvas/ActivityDrawer.test.tsx`:

```tsx
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { ActivityDrawer } from './ActivityDrawer'

vi.mock('../../services/project.service', () => ({
  default: {
    activity: vi.fn(),
  },
}))

import projectService from '../../services/project.service'

const ENTRY_FIXTURES = [
  {
    id: 'a1',
    action: 'layout.saved',
    timestamp: new Date(Date.now() - 5 * 60_000).toISOString(),
  },
  {
    id: 'a2',
    action: 'design.generated',
    timestamp: new Date(Date.now() - 10 * 60_000).toISOString(),
  },
]

beforeEach(() => {
  vi.mocked(projectService.activity).mockReset()
})

describe('ActivityDrawer', () => {
  it('renders rows with human-friendly labels when open', async () => {
    vi.mocked(projectService.activity).mockResolvedValue(ENTRY_FIXTURES)

    render(
      <ActivityDrawer projectId="p1" open={true} onClose={vi.fn()} />
    )

    await waitFor(() =>
      expect(screen.getByText('Saved layout')).toBeInTheDocument()
    )
    expect(screen.getByText('Generated layout')).toBeInTheDocument()
  })

  it('renders empty state when API returns an empty list', async () => {
    vi.mocked(projectService.activity).mockResolvedValue([])

    render(
      <ActivityDrawer projectId="p1" open={true} onClose={vi.fn()} />
    )

    await waitFor(() =>
      expect(screen.getByText('No activity yet.')).toBeInTheDocument()
    )
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && npm test -- src/components/canvas/ActivityDrawer.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `ActivityDrawer`**

Create `frontend/src/components/canvas/ActivityDrawer.tsx`:

```tsx
import { useEffect, useRef, useState } from 'react'
import projectService, { ActivityEntry } from '../../services/project.service'
import { formatRelative } from '../../utils/time'

interface Props {
  projectId: string
  open: boolean
  onClose: () => void
}

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

export function ActivityDrawer({ projectId, open, onClose }: Props) {
  const [entries, setEntries] = useState<ActivityEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isMounted = useRef(true)

  useEffect(() => {
    isMounted.current = true
    return () => {
      isMounted.current = false
    }
  }, [])

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
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && npm test -- src/components/canvas/ActivityDrawer.test.tsx
```

Expected: 2 PASS.

- [ ] **Step 5: Run the full frontend suite**

```bash
cd frontend && npm test 2>&1 | tail -3
```

Expected: 33 passed (31 baseline + 2 new).

- [ ] **Step 6: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/canvas/ActivityDrawer.tsx frontend/src/components/canvas/ActivityDrawer.test.tsx
git commit -m "feat(sprint9b): ActivityDrawer component with rows + empty state"
```

---

### Task 11: Wire Activity button into Project page

**Files:**
- Modify: `frontend/src/pages/Project/index.tsx`
- Modify: `frontend/src/pages/Project/index.test.tsx`

- [ ] **Step 1: Write the failing test**

Append to the existing `describe('ProjectPage history drawer')` block in `frontend/src/pages/Project/index.test.tsx`:

```tsx
  it('opens the activity drawer when the Activity button is clicked', async () => {
    renderProjectPage()

    const activityButton = await screen.findByRole('button', { name: 'Activity' })
    await userEvent.click(activityButton)

    expect(screen.getByRole('dialog', { name: 'Project activity' })).toBeInTheDocument()
  })
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx
```

Expected: FAIL — `Activity` button not found.

- [ ] **Step 3: Add import + state + button + drawer mount**

In `frontend/src/pages/Project/index.tsx`:

a. Add the import (after the existing `VersionHistoryDrawer` import):

```tsx
import { ActivityDrawer } from '../../components/canvas/ActivityDrawer'
```

b. Add the state (right after the existing `historyOpen` declaration):

```tsx
const [activityOpen, setActivityOpen] = useState(false)
```

c. Add the Activity button immediately AFTER the existing History button in the non-editing top-bar group. The relevant block currently looks like:

```tsx
<Button variant="secondary" onClick={() => setHistoryOpen(true)}>
  History
</Button>
```

Insert the Activity button right after it:

```tsx
<Button variant="secondary" onClick={() => setActivityOpen(true)}>
  Activity
</Button>
```

d. Mount the drawer right after the existing `<VersionHistoryDrawer>` mount near the bottom of the JSX:

```tsx
<ActivityDrawer
  projectId={id!}
  open={activityOpen}
  onClose={() => setActivityOpen(false)}
/>
```

- [ ] **Step 4: Run the new test**

```bash
cd frontend && npm test -- src/pages/Project/index.test.tsx 2>&1 | tail -8
```

Expected: all Project page tests pass (including the new one — total 6 in the file).

- [ ] **Step 5: Run the full frontend suite**

```bash
cd frontend && npm test 2>&1 | tail -3
```

Expected: 34 passed.

- [ ] **Step 6: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/Project/index.tsx frontend/src/pages/Project/index.test.tsx
git commit -m "feat(sprint9b): Activity button + ActivityDrawer on Project page"
```

---

### Task 12: Update CLAUDE.md + final verification + push

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Update Sprint 9 sub-block in CLAUDE.md**

Find the line `### Sprint 9B — Activity Log Panel ⏳ Not Started` and replace it with:

```markdown
### Sprint 9B — Activity Log Panel ✅ Complete

- [x] Alembic `006` adds nullable, indexed `project_id` to `activity_logs` (no FK — append-only audit)
- [x] `ActivityLog.project_id` declared on the model
- [x] `log_activity(db, user_id, action, project_id=None)` — all 7 existing call sites pass `project_id`
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
```

- [ ] **Step 2: Run final backend tests**

```bash
cd backend && DATABASE_URL=sqlite+aiosqlite:///:memory: SECRET_KEY=test-secret-key pytest -q 2>&1 | tail -3
```

Expected: 90 passed, 0 failures.

- [ ] **Step 3: Run final frontend tests**

```bash
cd frontend && npm test 2>&1 | tail -3
```

Expected: 34 passed.

- [ ] **Step 4: TypeScript check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(sprint9b): mark Sprint 9B complete in CLAUDE.md"
```

- [ ] **Step 6: Push the branch + list commits**

```bash
git push -u origin sprint-9b/activity-log
git log $(git merge-base sprint-9a/version-history HEAD)..HEAD --oneline
```

---

## Definition of Done

- [ ] All 12 tasks complete
- [ ] Backend: 90 passing, 0 failures
- [ ] Frontend: 34 passing, 0 failures
- [ ] `npx tsc --noEmit` clean
- [ ] `docker-compose up` — Activity button opens the drawer, recent actions render with friendly labels
- [ ] Branch pushed; PR opened (after Sprint 9A merges) targeting `main`
