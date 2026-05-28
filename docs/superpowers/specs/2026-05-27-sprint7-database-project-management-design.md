# Sprint 7 — Database and Project Management: Design Spec

**Date:** 2026-05-27
**Status:** Backfilled — implementation merged to `main` before this spec was written. This document describes the design that was actually shipped, so future agents have a reference matching the code.
**Sprint Goal:** Projects feel like real, persistent design files: every save creates a versioned snapshot, the dashboard previews each project with a thumbnail, projects can be duplicated, and deleting a project cleans up all of its layouts.

---

## Context

Builds on Sprint 6, which landed the Design and DesignVersion tables (Alembic `004`) and the in-app editing workflow. Sprint 6 already writes `version_name`, `version_type`, and `change_summary` through the SQLAlchemy model — but those columns don't exist until Sprint 7's migration runs. Sprint 7 adds the columns, exposes the version history through an API, and wires duplication, deletion-with-cascade, and thumbnails through to the dashboard.

These files already exist and are extended rather than rewritten:

- `backend/app/api/projects/router.py` — adds two endpoints
- `backend/app/services/project_service.py` — gains `list_project_versions`, `duplicate_project`, cascading delete
- `backend/app/services/design_service.py` — `update_design_layout` writes `thumbnail_url` to the project
- `backend/app/schemas/project.py` — `ProjectVersionOut`, `thumbnail_url` on `ProjectOut`
- `frontend/src/services/project.service.ts` — `duplicate`, `versions`
- `frontend/src/components/projects/ProjectCard.tsx` — renders thumbnails
- `frontend/src/pages/Project/index.tsx` — Duplicate button, version name/summary inputs, thumbnail capture

---

## Scope

### In scope

- Alembic migration `005_sprint7_project_management.py`:
    - `projects.thumbnail_url TEXT NULL`
    - `design_versions.version_name VARCHAR(200) NULL`
    - `design_versions.version_type VARCHAR(50) NULL`
    - `design_versions.change_summary TEXT NULL`
- `Project.thumbnail_url` and `DesignVersion.version_name` / `version_type` / `change_summary` on the SQLAlchemy models
- `GET /api/projects/{id}/versions` — returns versions newest first
- `POST /api/projects/{id}/duplicate` — copies the project and its latest design layout into a new project
- `DELETE /api/projects/{id}` — cascades to delete the project's `Design` and `DesignVersion` rows first so the FK doesn't block deletion
- `PUT /api/design/{id}` — when `thumbnailUrl` is non-null, persists it to `projects.thumbnail_url`
- `ProjectVersionOut` Pydantic schema
- Frontend `projectService.duplicate(id)` and `projectService.versions(id)`
- Frontend `ProjectCard` displays `thumbnail_url` or a "No preview yet" placeholder
- Project page: Duplicate button, Version Name + Change Summary inputs, thumbnail capture on Save Layout, empty state when no saved layout exists
- Save status distinguishes Unsaved / Saving / Saved (with timestamp) / Error in the EditorToolbar (already added in Sprint 6, reaffirmed here)

### Out of scope

- Full version history panel and restore UI → Sprint 9
- Collaboration / role-based sharing → Sprint 9
- Persistent (DB-backed) per-object activity log → Sprint 9
- Public share links / read-only project view → Sprint 12

---

## Architecture

### Save Layout end-to-end

```text
[Editor] Save Layout button
  ├── const thumbnailUrl = canvas.toDataURL('image/png')   // dataURL string or null
  └── PUT /api/design/{designId} {
        layout: serializeLayout(),
        versionName, changeSummary, thumbnailUrl,
      }
        └── design_service.update_design_layout()
              ├── owns-design check (403)
              ├── next_version = MAX(version_number) + 1
              ├── UPDATE designs SET layout_json, updated_at = now()
              ├── if thumbnail_url not null:
              │     UPDATE projects SET thumbnail_url, updated_at = now()
              └── INSERT DesignVersion(
                    version_number = next_version,
                    version_name   = body.versionName  or f"Manual save v{n}",
                    version_type   = 'manual',
                    change_summary = body.changeSummary or 'Manual layout save',
                    layout_json,
                    prompt_used    = layout.metadata.prompt,
                  )
        └── ActivityLog "layout.saved"

[Dashboard] mounts
  └── GET /api/projects
       └── each ProjectCard renders project.thumbnail_url or "No preview yet"
```

### Duplicate

```text
POST /api/projects/{id}/duplicate
  └── project_service.duplicate_project()
        ├── load source (403 / 404)
        ├── INSERT Project(
        │     title = "Copy of {source.title}",
        │     description = source.description,
        │     thumbnail_url = source.thumbnail_url,
        │   )
        ├── if source has a Design:
        │     INSERT Design(project_id = copy.id, layout_json = deepcopy(source layout))
        │     INSERT DesignVersion(
        │       version_number = 1,
        │       version_type = 'duplicate',
        │       version_name = 'Duplicated project',
        │       change_summary = f"Copied from {source.title}",
        │       layout_json = deepcopy,
        │     )
        ├── set copy.updated_at = now()
        └── ActivityLog "project.duplicated"
```

The deepcopy is important: layout JSON contains nested dicts/lists, and SQLAlchemy reuses the loaded object graph by reference. Without `deepcopy`, mutating one project's layout would mutate the other.

### Delete (cascade)

```text
DELETE /api/projects/{id}
  └── _get_owned_project (403 / 404)
  └── DELETE FROM design_versions WHERE project_id = ?
  └── DELETE FROM designs WHERE project_id = ?
  └── db.delete(project)  → DELETE FROM projects WHERE id = ?
  └── ActivityLog "project.deleted"
```

`DesignVersion` has FKs both to `designs.id` and `projects.id`, so we drop versions before designs. The order is enforced in `delete_project` rather than via DB-level `ON DELETE CASCADE` because the current migrations omit the cascade modifier.

---

## File Map

```text
backend/
├── alembic/versions/
│   └── 005_sprint7_project_management.py  CREATE
├── app/
│   ├── api/projects/router.py              MODIFY (versions, duplicate)
│   ├── models/
│   │   ├── design_version.py               MODIFY (version_name, version_type, change_summary)
│   │   └── project.py                      MODIFY (thumbnail_url)
│   ├── schemas/project.py                  MODIFY (ProjectVersionOut, thumbnail_url on ProjectOut)
│   ├── services/
│   │   ├── design_service.py               MODIFY (thumbnail_url persistence in update_design_layout)
│   │   └── project_service.py              MODIFY (list_project_versions, duplicate_project, cascade delete)
│   └── tests/test_projects.py              EXPAND (versions, duplicate, cascade delete)

frontend/src/
├── components/projects/ProjectCard.tsx     MODIFY (thumbnail or placeholder)
├── pages/Project/index.tsx                 MODIFY (Duplicate, versionName/changeSummary inputs, thumbnail capture)
├── services/project.service.ts             MODIFY (duplicate, versions, thumbnail_url on Project)
└── store/canvasStore.test.ts               EXPAND (empty layout, multi-floor load/serialize)
```

---

## Backend: Alembic `005_sprint7_project_management.py`

```python
def upgrade() -> None:
    op.add_column("projects", sa.Column("thumbnail_url", sa.Text(), nullable=True))
    op.add_column("design_versions", sa.Column("version_name", sa.String(length=200), nullable=True))
    op.add_column("design_versions", sa.Column("version_type", sa.String(length=50), nullable=True))
    op.add_column("design_versions", sa.Column("change_summary", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("design_versions", "change_summary")
    op.drop_column("design_versions", "version_type")
    op.drop_column("design_versions", "version_name")
    op.drop_column("projects", "thumbnail_url")
```

Three nullable text/varchar columns on `design_versions`, one on `projects`. All nullable so historical rows from Sprint 6 (if any reached prod) continue to load. No data backfill required.

---

## Backend: Schemas

### `ProjectOut` (extended)

Adds `thumbnail_url: str | None = None`. Stays compatible with existing clients.

### `ProjectVersionOut` (new)

```python
class ProjectVersionOut(BaseModel):
    id: str
    design_id: str
    project_id: str
    version_number: int
    version_name: str | None = None
    version_type: str | None = None
    change_summary: str | None = None
    created_by: str          # mapped from DesignVersion.user_id
    created_at: datetime

    model_config = {"from_attributes": True}
```

`created_by` is the user who saved the version. It maps from `DesignVersion.user_id`; the service layer builds the response manually so the field name flips from `user_id` to the more user-meaningful `created_by`.

---

## Backend: Services

### `list_project_versions(db, user_id, project_id)`

```python
await _get_owned_project(db, user_id, project_id)  # 403/404
result = await db.execute(
    select(DesignVersion)
    .where(DesignVersion.project_id == project_id)
    .order_by(desc(DesignVersion.created_at), desc(DesignVersion.version_number))
)
versions = result.scalars().all()
return [ProjectVersionOut(... mapping user_id → created_by ...) for v in versions]
```

Ordering by `created_at DESC` first means versions saved within the same second still come back in the right order (`version_number DESC` tiebreaker).

### `duplicate_project(db, user_id, project_id)`

1. Load source project (403/404).
2. Insert new project: `title = "Copy of {source.title}"`, copy description, copy `thumbnail_url`.
3. `await db.flush()` to materialise the new project ID for FK use.
4. Query for the source's latest `Design` (`ORDER BY updated_at DESC LIMIT 1`).
5. If a source design exists:
    - Insert new `Design(project_id=copy.id, user_id, layout_json=deepcopy(source))`.
    - Flush again.
    - Insert `DesignVersion(version_number=1, version_type='duplicate', version_name='Duplicated project', change_summary=f"Copied from {source.title}", layout_json=deepcopy)`.
6. Set `duplicate.updated_at = now()` so the copy sorts to the top on the dashboard.
7. Commit, refresh, log `project.duplicated`.

The copy starts at `version_number = 1` — versions reset for the new project rather than continuing the source's numbering.

### `delete_project(db, user_id, project_id)` (modified)

```python
project = await _get_owned_project(db, user_id, project_id)
await db.execute(delete(DesignVersion).where(DesignVersion.project_id == project_id))
await db.execute(delete(Design).where(Design.project_id == project_id))
await db.delete(project)
await db.commit()
await log_activity(db, user_id, "project.deleted")
```

Sprint 2 didn't add cascade, so projects with attached designs would have failed to delete with an FK violation. Sprint 7 removes design versions first, then designs, then the project.

### `update_design_layout` (thumbnail addition)

```python
project_result = await db.execute(select(Project).where(Project.id == design.project_id))
project = project_result.scalar_one_or_none()
if project is not None:
    if thumbnail_url is not None:
        project.thumbnail_url = thumbnail_url
    project.updated_at = datetime.now(timezone.utc)
```

When the frontend sends `thumbnailUrl`, it overrides the previous value; when it sends `null` or omits the field, the existing thumbnail is preserved. Either way, `projects.updated_at` is bumped so the dashboard re-sorts.

---

## Backend: API

### `GET /api/projects/{project_id}/versions`

**Auth:** Required.
**Response:** `200 [ProjectVersionOut]` ordered newest first.
**Errors:** `404` if the project doesn't exist; `403` if it belongs to another user.

### `POST /api/projects/{project_id}/duplicate`

**Auth:** Required.
**Response:** `201 ProjectOut` (the new project).
**Errors:** `404`/`403` as above.

### `DELETE /api/projects/{project_id}` (behavioural change)

Returns `204` even when designs exist for the project. Cascade is handled in the service layer.

---

## Frontend: Service Layer

### `project.service.ts`

```typescript
export interface Project {
  id: string
  user_id: string
  title: string
  description: string | null
  thumbnail_url?: string | null
  created_at: string
  updated_at: string
}

export interface ProjectVersion {
  id: string
  design_id: string
  project_id: string
  version_number: number
  version_name?: string | null
  version_type?: string | null
  change_summary?: string | null
  created_by: string
  created_at: string
}

const projectService = {
  list, get, create, update, delete,
  duplicate: (id) => api.post(`/api/projects/${id}/duplicate`).then(r => r.data),
  versions:  (id) => api.get (`/api/projects/${id}/versions` ).then(r => r.data),
}
```

### `design.service.ts` (extended)

`saveDesignLayout` already accepts `thumbnailUrl` in its options object (Sprint 6 wired the request shape). Sprint 7 is where the backend actually persists it.

---

## Frontend: Components

### `ProjectCard`

```tsx
{project.thumbnail_url ? (
  <img src={project.thumbnail_url} alt="" className="h-36 w-full bg-gray-100 object-cover" />
) : (
  <div className="flex h-36 w-full items-center justify-center bg-gray-100 text-xs font-medium text-gray-400">
    No preview yet
  </div>
)}
```

The card always reserves a fixed-height thumbnail row so the dashboard grid stays aligned even when some projects have no preview.

### `Project` page additions

```tsx
<input value={versionName} onChange={(e) => setVersionName(e.target.value)}
       placeholder="Version name (optional)" ... />
<input value={changeSummary} onChange={(e) => setChangeSummary(e.target.value)}
       placeholder="Change summary (optional)" ... />
<Button variant="secondary" onClick={handleSaveLayout}
        loading={layoutSaving} disabled={!designId || layoutSaving}>
  Save Layout
</Button>
<Button variant="secondary" onClick={handleDuplicate}
        loading={duplicating} disabled={duplicating}>
  Duplicate
</Button>
```

`handleDuplicate` calls `projectService.duplicate(id)` and `navigate(`/projects/${duplicate.id}`)` so the user lands in the copy.

`handleSaveLayout` (extended from Sprint 6) captures the thumbnail via `canvas.toDataURL('image/png')`. When the request succeeds, the project's local state is patched with the new `thumbnail_url` so the user can see immediate confirmation without re-fetching.

---

## Testing

### Backend — `test_projects.py` (additions)

1. `test_project_versions_api_returns_versions_newest_first` — generate a layout, save with a manual `versionName`, GET `/versions` returns `[v=2, v=1]` with `version_name`, `version_type='manual'`, `change_summary`, `created_by` populated.
2. `test_project_versions_wrong_user_forbidden` — token B fetching token A's versions gets 403.
3. `test_duplicate_project_copies_latest_design_layout_and_thumbnail` — edit, save with thumbnail, duplicate; the new project has `"Copy of <title>"`, the same thumbnail dataURL, and `/latest` returns the edited rooms with a fresh `designId`. The duplicate's first DesignVersion has `version_number=1`, `version_type='duplicate'`.
4. `test_delete_project_with_designs_succeeds` — generate a design then DELETE the project; expect 204 and no orphan `Design` or `DesignVersion` rows.

### Backend — `test_designs.py` (additions)

5. `test_manual_save_stores_version_metadata_and_thumbnail` — PUT a design with `versionName`, `changeSummary`, `thumbnailUrl`. Verify the new `DesignVersion` row has the correct metadata, the saved layout matches the request, and `Project.thumbnail_url` is set.

### Frontend — `canvasStore.test.ts` (additions for Sprint 7-relevant flows)

1. `clearLayout` empties rooms, nulls `designId`/`designVersionId`, resets `saveStatus` to `'saved'`
2. `loadLayout` for multi-floor layouts populates `floors[]`, defaults `selectedFloor` to the first floor, and routes upper rooms to the right `floorLevel`
3. `serializeLayout` groups rooms back into their floors and reports `metadata.totalFloors`

---

## Error Handling

| Scenario | Status / Behaviour |
|---|---|
| Duplicate a project that doesn't exist | 404 |
| Duplicate another user's project | 403 |
| List versions for another user's project | 403 |
| Save Layout when `thumbnailUrl` capture fails (canvas tainted, e.g. cross-origin texture) | `captureCanvasThumbnail` returns `null` → backend leaves `thumbnail_url` untouched; the rest of the save succeeds |
| Delete a project that already has designs | Cascade succeeds; 204 |
| Frontend save failure | `saveStatus = 'error'`, `layoutSaveError` shown beneath Save Layout button |

---

## Definition of Done

- [x] Alembic `005` adds `projects.thumbnail_url`, `design_versions.version_name`/`version_type`/`change_summary`
- [x] `update_design_layout` persists `thumbnailUrl` to the project when provided
- [x] `GET /api/projects/{id}/versions` returns ordered versions with `created_by`
- [x] `POST /api/projects/{id}/duplicate` copies project + latest design with `deepcopy`
- [x] `DELETE /api/projects/{id}` removes designs and versions before the project row
- [x] `ProjectCard` renders `thumbnail_url` or a "No preview yet" placeholder
- [x] Project page exposes Duplicate, Version Name, Change Summary, and captures a thumbnail on Save Layout
- [x] Save status communicates Unsaved / Saving / Saved (with timestamp) / Error
- [x] Backend tests cover versions, duplicate, cascade delete, thumbnail persistence
- [x] Frontend canvas store tests cover `clearLayout`, multi-floor load/serialize
- [x] `npx tsc --noEmit` passes
- [ ] Full version history panel — deferred to Sprint 9
- [ ] Restore-from-version UI — deferred to Sprint 9
