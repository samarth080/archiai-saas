# Sprint 6 — 3D Editing Workflow: Design Spec

**Date:** 2026-05-27
**Status:** Backfilled — implementation merged to `main` before this spec was written. This document describes the design that was actually shipped, so future agents have a reference matching the code.
**Sprint Goal:** Users have a complete in-browser editing toolkit for the current generated layout: select, drag, resize, rotate, label, duplicate, delete, snap-to-grid, add new objects, switch floors, and persist edits to the database with named versions.

---

## Context

Builds on Sprint 5 (prompt → layout generation, in-memory canvas). The following already exist and are extended rather than rewritten:

- `frontend/src/store/canvasStore.ts` — Zustand canvas store (heavily expanded)
- `frontend/src/components/canvas/Canvas3D.tsx`, `Scene.tsx`, `RoomMesh.tsx`, `Inspector.tsx` — modified for editing UX
- `frontend/src/pages/Project/index.tsx` — gains keyboard shortcuts, Save Layout, empty state
- `backend/app/services/prompt_service.py`, `layout_service.py` — extended for multi-floor extraction and placement
- `backend/app/api/designs/router.py` — gains `/project/{id}/latest` and `PUT /{design_id}`

This sprint also lands the Design + DesignVersion database tables that were deferred from Sprint 5, so the editing workflow can persist layouts immediately rather than waiting for Sprint 7.

---

## Scope

### In scope

- Canvas object types beyond `room`: `wall`, `door`, `window`, `stair`, `floor`, `open_space`
- Multi-floor layouts: `floors[]`, floor selector, per-floor add/edit
- Direct pointer drag on the X/Z plane (replaces the Sprint 4 `TransformControls` gizmo)
- Snap-to-grid toggle for drag and inspector positions
- Object rotation (X / Y / Z degrees), kept in `Room.rotation`
- Object labels rendered as HTML sprites above each mesh
- Inspector: label, object type, floor, position (X/Z), size (W/D/H), rotation (X/Y/Z), Duplicate, Delete, recent edit list
- Editor toolbar: save status, snap toggle, floor selector, add-object picker, Duplicate, Delete
- Keyboard shortcuts: Ctrl/Cmd+D duplicate, Delete/Backspace delete
- In-memory activity log of recent edits (latest 5 visible in Inspector)
- `Design` + `DesignVersion` SQLAlchemy models and Alembic migration `004`
- Project-scoped generation: `POST /api/design/generate` saves a `Design` and first `DesignVersion` when `projectId` is supplied
- `GET /api/design/project/{project_id}/latest` returns the most-recently-updated design for the project
- `PUT /api/design/{design_id}` saves the current layout and creates the next `DesignVersion`
- ActivityLog entries: `design.generated`, `layout.saved`

### Out of scope

- Thumbnails on the dashboard → Sprint 7
- Project duplicate, version list endpoint → Sprint 7
- Restore-from-version UI, named version timeline → Sprint 9
- Persistent (DB-backed) per-object activity log → Sprint 9
- Real-time collaboration → Sprint 9

---

## Architecture

### Backend flow

```text
POST /api/design/generate { prompt, projectId? }
  → prompt_service.extract_rooms(prompt) → List[RoomSpec]
  → prompt_service.detect_building_type(prompt) → str
  → prompt_service.extract_total_floors(prompt) → int (default 1)
  → layout_service.generate_layout(specs, total_floors=N) → layout dict
        ├── _assign_rooms_to_floors() — distributes rooms zone-by-zone, level-by-level
        └── _place_rooms() — left-to-right with 1m gap, 2m between zones
  → if projectId: design_service.save_generated_design()
        ├── INSERT Design(project_id, user_id, layout_json)
        └── INSERT DesignVersion(version_number=1, version_type='generated', ...)
  → ActivityLog "design.generated"
  → 200 GenerateResponse

GET /api/design/project/{project_id}/latest
  → owns-project check (403 / 404)
  → SELECT Design WHERE project_id ORDER BY updated_at DESC LIMIT 1
  → SELECT DesignVersion WHERE design_id ORDER BY version_number DESC LIMIT 1
  → 200 GenerateResponse with designId/designVersionId

PUT /api/design/{design_id} { layout, versionName?, changeSummary?, thumbnailUrl? }
  → owns-design check
  → MAX(version_number) + 1
  → UPDATE designs SET layout_json, updated_at
  → INSERT DesignVersion(version_type='manual', version_name, change_summary, ...)
  → ActivityLog "layout.saved"
  → 200 GenerateResponse
```

Note: `thumbnailUrl` is accepted on the schema in Sprint 6 but only persisted to `projects.thumbnail_url` once Sprint 7's migration adds that column. Sprint 6 alone leaves the field unused; the request shape is forward-compatible.

### Frontend flow

```text
Project page mounts → GET /api/projects/:id
  → GET /api/design/project/:id/latest
      ├── 200 → canvasStore.loadLayout(layout) (designId + designVersionId tracked)
      └── 404 → canvasStore.clearLayout(); show empty state

User types prompt → Generate
  → POST /api/design/generate { prompt, projectId }
  → canvasStore.loadLayout(result)

User drags a room
  → RoomMesh.onPointerDown → selectRoom + orbit disabled + pointer capture
  → onPointerMove → updateRoom({ position }, { log: false }) (no save churn while dragging)
  → onPointerUp → updateRoom({ position }, { action: 'object.moved', previousValue: start })
       → logs activity + saveStatus = 'unsaved'

User clicks Save Layout (in top bar)
  → captureCanvasThumbnail() via canvas.toDataURL('image/png')
  → PUT /api/design/:designId { layout, versionName, changeSummary, thumbnailUrl }
  → on 200: canvasStore.loadLayout(result) → saveStatus = 'saved'
  → on error: saveStatus = 'error'
```

---

## File Map

```text
backend/
├── alembic/versions/
│   └── 004_create_designs.py           CREATE (designs, design_versions)
├── app/
│   ├── api/designs/router.py           MODIFY (project_id param, /latest, PUT /{id})
│   ├── models/
│   │   ├── design.py                   CREATE
│   │   └── design_version.py           CREATE
│   ├── schemas/design.py               MODIFY (projectId, SaveDesignRequest, floors/building, rotation)
│   ├── services/
│   │   ├── design_service.py           CREATE (save_generated_design, get_latest_project_design, update_design_layout)
│   │   ├── layout_service.py           MODIFY (multi-floor, stairs, x_offset)
│   │   └── prompt_service.py           MODIFY (extract_total_floors)
│   └── tests/test_designs.py           CREATE / EXPAND

frontend/src/
├── components/canvas/
│   ├── Canvas3D.tsx                    MODIFY (keyboard shortcuts, floor filtering, onPointerMissed)
│   ├── EditorToolbar.tsx               CREATE
│   ├── Inspector.tsx                   REWRITE (type, floor, rotation, duplicate, activity)
│   ├── RoomMesh.tsx                    REWRITE (direct drag, label sprite, highlight outline)
│   └── Scene.tsx                       MODIFY (lighting/grid kept; no transform controls)
├── pages/Project/index.tsx             MODIFY (load latest, Save Layout, version inputs, empty state)
├── services/design.service.ts          MODIFY (getLatestProjectDesign, saveDesignLayout, projectId)
└── store/canvasStore.ts                REWRITE (object types, floors, snap, save status, activity log)
```

---

## Backend: Database Models

### `designs`

| Column | Type | Notes |
|---|---|---|
| `id` | String PK | UUID4 |
| `project_id` | FK → projects.id | indexed |
| `user_id` | FK → users.id | indexed |
| `layout_json` | JSON | latest saved layout |
| `created_at`, `updated_at` | timestamptz | server default `now()` |

One Design per project (in practice the latest by `updated_at` is "the" design). The endpoint that fetches a project's latest design returns the row with the most recent `updated_at`.

### `design_versions`

| Column | Type | Notes |
|---|---|---|
| `id` | String PK | UUID4 |
| `design_id` | FK → designs.id | indexed |
| `project_id` | FK → projects.id | indexed (denormalised for listing) |
| `user_id` | FK → users.id | indexed |
| `version_number` | Integer | monotonic per `design_id`, starts at 1 |
| `version_name` | String(200) nullable | added by Sprint 7 migration; written by Sprint 6 code |
| `version_type` | String(50) nullable | `generated` / `manual` |
| `change_summary` | Text nullable | free text |
| `layout_json` | JSON | snapshot at this version |
| `prompt_used` | Text nullable | snapshot of the prompt for generated/manual versions |
| `created_at` | timestamptz | server default `now()` |

**Note on `version_name` / `version_type` / `change_summary`:** these columns are added by Alembic `005` (Sprint 7). Sprint 6 writes them anyway since the SQLAlchemy model declares them as nullable, and the columns become available once `005` runs. Sprint 6 cannot be deployed without Sprint 7's migration applied — the two land together in this monorepo.

### Alembic `004_create_designs.py`

Creates `designs` and `design_versions` with the columns above (excluding the three Sprint-7-only columns). Indexes on every FK column.

---

## Backend: Prompt Service — Multi-floor Extraction

`extract_total_floors(prompt: str) -> int` returns the number of floors (default 1). It scans in this order, returning the first match:

| Pattern | Example | Result |
|---|---|---|
| `g\s*\+\s*(\d+)` | `"G+2 villa"` | `3` (ground + 2 upper) |
| `ground\s+plus\s+(N)` | `"ground plus two"` | `3` |
| `(N)\s+(floors?\|storeys?\|story\|stories)` | `"3 floor house"` / `"two storeys"` | `N` |

`N` may be a digit or a word number (`one`…`ten`). The regex shares the `_COUNT_ALTS` alternation with `extract_rooms`, so the supported number words stay in sync.

---

## Backend: Layout Service — Multi-floor Placement

```python
def generate_layout(
    room_specs: list[RoomSpec],
    prompt: str = "",
    building_type: str = "apartment",
    total_floors: int = 1,
) -> dict
```

### Floor assignment (`_assign_rooms_to_floors`)

For `total_floors > 1`:

- `living_room`, `kitchen`, `dining_room`, `hallway`, `garage` → ground floor (level 0)
- `bathroom` → first occurrence ground, subsequent ones cycle through upper floors
- `bedroom` / `master_bedroom` → cycle through upper levels (`1..total_floors-1`)
- If no `master_bedroom` exists, the first `bedroom` is promoted to `master_bedroom`
- `balcony`, `utility` → top floor
- Anything else → cycle through upper levels

For `total_floors == 1`, all specs go to level 0.

### Placement (`_place_rooms`)

For each floor: groups specs into Public / Private / Other zones (same partition as Sprint 5), places left-to-right per zone with 1m gaps and 2m between zones, computing `position` as the mesh centre (`x = current_x + w/2`, `y = elevation + h/2`, `z = current_z + d/2`). For multi-floor layouts, every floor reserves the left-most slot for a `Stairs` mesh aligned vertically, and rooms start at `x = _STAIRS_SIZE.w + 1m`.

### Stairs placeholder (`_add_stairs`)

Each upper-floor-bearing layout (`total_floors > 1`) includes one `Stairs` object per floor at a fixed `(x, z)` of `(1.0, 1.5)` and full floor height (`h = _FLOOR_HEIGHT = 3.2`). They render as a column of stacked stair meshes so users can see vertical alignment.

### Output shape

```json
{
  "version": "1.0",
  "metadata": {
    "prompt": "...",
    "building_type": "house",
    "buildingType": "house",
    "style": "modern",
    "room_count": 9,
    "totalFloors": 2,
    "totalRooms": 8,
    "totalAreaSqm": 142.0
  },
  "building": { "floorHeight": 3.2 },
  "floors": [
    {
      "id": "floor_0",
      "name": "Ground Floor",
      "level": 0,
      "elevation": 0.0,
      "rooms": [ /* Stairs first if multi-floor, then placed rooms */ ]
    }
  ],
  "rooms": [ /* flat array of every floor's rooms — kept for backward compatibility */ ]
}
```

Every room object includes `roomType`, `objectType`, `floorId`, `floorLevel`, `position`, `size`, `color`. `rotation` is absent from generated rooms and defaults to `{x: 0, y: 0, z: 0}` on the frontend.

---

## Backend: API Endpoints

### `POST /api/design/generate`

**Request (extends Sprint 5):**
```python
class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=5)
    project_id: str | None = Field(default=None, alias="projectId")
    model_config = {"populate_by_name": True}
```

**Behaviour:**
- Returns layout as before
- If `projectId` is provided: validates the project belongs to the user, inserts a `Design` and `DesignVersion(version_number=1, version_type='generated')`, returns the layout with `designId` and `designVersionId` populated
- Logs `design.generated` to ActivityLog regardless of whether a Design was persisted

### `GET /api/design/project/{project_id}/latest`

**Auth:** Required.
**Behaviour:** Returns the latest-updated `Design` for the project along with its most recent `DesignVersion`. 404 if the project has no design yet; 403 if the project belongs to another user.

### `PUT /api/design/{design_id}`

**Request:**
```python
class SaveDesignRequest(BaseModel):
    layout: dict[str, Any]
    version_name: str | None = Field(default=None, alias="versionName")
    change_summary: str | None = Field(default=None, alias="changeSummary")
    thumbnail_url: str | None = Field(default=None, alias="thumbnailUrl")
    model_config = {"populate_by_name": True}
```

**Behaviour:**
- 403 if `design.user_id != user_id`
- Reads `MAX(version_number)` for the design, inserts a new version with `version_number = max + 1`, `version_type='manual'`, default `version_name = "Manual save v{n}"`, default `change_summary = "Manual layout save"`
- Updates `designs.layout_json` and `designs.updated_at`
- When `thumbnail_url` is non-null, also writes it to `projects.thumbnail_url` and bumps `projects.updated_at` (effective only after Alembic 005)
- Logs `layout.saved`

### Error responses

| Scenario | Status | Notes |
|---|---|---|
| Missing Bearer token | 401 | `Not authenticated` |
| Project not found | 404 | `Project not found` |
| Project belongs to another user | 403 | `Access forbidden` |
| Design not found | 404 | `Design not found` |
| Prompt < 5 chars | 422 | Pydantic |
| No rooms detected | 422 | `No rooms detected. Try: '2 bedroom apartment with kitchen'` |

---

## Frontend: Canvas Store

Major additions vs. Sprint 5:

### Types

```typescript
type CanvasObjectType = 'room' | 'wall' | 'door' | 'window' | 'stair' | 'floor' | 'open_space'
type CanvasEditAction = 'object.added' | 'object.deleted' | 'object.duplicated'
                      | 'object.moved' | 'object.resized' | 'object.rotated'
                      | 'object.renamed' | 'object.updated'
type SaveStatus = 'saved' | 'saving' | 'unsaved' | 'error'

interface Room {
  id: string
  label: string
  roomType?: string
  objectType: CanvasObjectType
  floorId?: string
  floorLevel?: number
  position: { x: number; y: number; z: number }
  size: { w: number; h: number; d: number }
  rotation: { x: number; y: number; z: number }
  color: string
}

interface CanvasFloor {
  id: string
  name: string
  level: number
  elevation: number
  rooms?: Room[]
}

interface CanvasLayout {
  version: string
  designId?: string
  designVersionId?: string
  metadata?: Record<string, unknown>
  building?: { floorHeight?: number }
  floors?: CanvasFloor[]
  rooms: Room[]
}
```

### State additions

```typescript
floors: CanvasFloor[]            // defaults to [DEFAULT_FLOOR]
selectedFloor: number | 'all'    // defaults to 0; 'all' shows every floor stacked
floorHeight: number              // default 3.2
designId: string | null
designVersionId: string | null
layoutMetadata: Record<string, unknown>
snapToGrid: boolean              // default false
gridSize: number                 // default 1 (metre)
saveStatus: SaveStatus           // default 'saved'
lastSavedAt: string | null
activityLog: CanvasActivityLogEntry[]
```

### New actions

| Action | Behaviour |
|---|---|
| `setSelectedFloor(floor)` | Switches floor view; deselects if the current selection isn't on the new floor |
| `setSnapToGrid(enabled)` | Toggles snap. Affects subsequent position writes |
| `updateRoom(id, patch, options)` | Snaps X/Z if enabled, recomputes Y when size changes (keeps box bottom on the floor elevation), appends to `activityLog` unless `options.log === false`, sets `saveStatus = 'unsaved'` |
| `deleteRoom(id)` | Removes; clears selection if it was selected; logs `object.deleted` |
| `duplicateRoom(id)` | Copies the room with `"<label> Copy"`, position offset by `gridSize`, selects the copy, logs `object.duplicated` |
| `duplicateSelected()` | Convenience for the Ctrl+D shortcut |
| `addObject(objectType)` | Creates a default object on the currently selected floor (`'all'` falls back to level 0). Uses `OBJECT_DEFAULTS[type]` for label/size/color |
| `loadLayout(layout)` | Normalises floors and rooms, sets `designId`/`designVersionId`, resets activity log, marks `saveStatus = 'saved'` |
| `clearLayout()` | Empties everything, returns to a single default floor |
| `serializeLayout()` | Returns a `CanvasLayout` with rooms grouped under their floors, plus updated metadata (`totalFloors`, `totalRooms`) |

### Object defaults

```typescript
const OBJECT_DEFAULTS: Record<CanvasObjectType, Pick<Room, 'label' | 'size' | 'color'>> = {
  room:       { label: 'Room',       size: { w: 4,    h: 3,    d: 4 },   color: '#818cf8' },
  wall:       { label: 'Wall',       size: { w: 6,    h: 2.8,  d: 0.25 }, color: '#94a3b8' },
  door:       { label: 'Door',       size: { w: 1,    h: 2.2,  d: 0.2 },  color: '#a16207' },
  window:     { label: 'Window',     size: { w: 1.4,  h: 1.2,  d: 0.18 }, color: '#38bdf8' },
  stair:      { label: 'Stair',      size: { w: 2.5,  h: 1,    d: 4 },    color: '#f97316' },
  floor:      { label: 'Floor',      size: { w: 8,    h: 0.15, d: 8 },    color: '#64748b' },
  open_space: { label: 'Open Space', size: { w: 5,    h: 0.1,  d: 5 },    color: '#22c55e' },
}
```

`normalizeRoom` and `normalizeLayout` accept legacy layouts that lack `objectType`/`rotation`/`floorId` so generated rooms from Sprint 5 still load cleanly.

---

## Frontend: RoomMesh — Direct Pointer Drag

Sprint 4 used `TransformControls` for moving rooms. Sprint 6 replaces that with direct pointer drag on the mesh itself, because the gizmo competed with selection events and made the inspector feel secondary.

### Drag algorithm

1. `onPointerDown` — `stopPropagation`, select this room, disable orbit controls, build a `THREE.Plane` at the room's Y, project the pointer ray onto it. Cache `dragStart`, `dragOffset` (pointer-to-room-centre delta), `dragPlane`, `dragPointerId`. Call `setPointerCapture(pointerId)` so the drag survives the cursor leaving the mesh.
2. `onPointerMove` — if the pointer ID matches and a drag is active, project ray onto the plane and call `updateRoom({ position }, { log: false })`. The `log: false` flag suppresses per-frame activity entries.
3. `onPointerUp` / `onPointerCancel` — re-enable orbit, compare `currentPosition` to `dragStart`; if moved (> 1 mm threshold) emit a single `object.moved` activity entry with the start as `previousValue`. Release pointer capture, clear refs.

Selection highlight is a `lineSegments`/`edgesGeometry` outline plus an emissive boost on the mesh material. The label is a `drei` `<Html>` sprite with `pointerEvents: 'none'` so it never blocks drag.

### Why not TransformControls?

The TransformControls wrapper was unstable: switching the selected mesh caused intermittent loss of click events. Removing it and adopting raycasted plane drag made selection and movement use the same pointer path, eliminating the bug.

---

## Frontend: Canvas3D

```tsx
<Canvas onPointerMissed={deselectAll}>
  <Scene orbitRef={orbitRef} />
  {visibleRooms.map((r) => <RoomMesh key={r.id} room={r} orbitRef={orbitRef} />)}
</Canvas>
```

`visibleRooms` filters by `selectedFloor` (or shows everything when `selectedFloor === 'all'`).

A single `useEffect` registers a `window` keydown listener:

| Key | Action |
|---|---|
| Ctrl/Cmd + D | `useCanvasStore.getState().duplicateSelected()` |
| Delete / Backspace (when not in a text field) | `deleteRoom(selectedId)` |

The handler bails out early when the focused element is an input/textarea/select/contentEditable so users can still type "d" in the prompt bar.

---

## Frontend: Inspector

Single right-hand panel, only rendered when something is selected. Sections, in order:

1. **Identity** — Label (text input), Type (dropdown across all `CanvasObjectType`), Floor (only shown when `floors.length > 1`).
2. **Position** — X and Z numeric inputs. Y is derived from floor elevation + height/2 and not editable directly.
3. **Size** — W / D / H. Each rejects values < 1 (`Math.max(1, n)`). Changing H recomputes Y so the bottom stays on the floor.
4. **Rotation** — X / Y / Z in degrees. `RoomMesh` converts to radians via `THREE.MathUtils.degToRad`.
5. **Actions** — Duplicate and Delete buttons (mirrors of the toolbar buttons).
6. **Recent edits** — last 5 entries from `activityLog`, each as `<action label> — <object label>`.

Every Inspector field call passes an explicit `{ action, previousValue }` so the activity log shows meaningful labels.

---

## Frontend: Editor Toolbar

Floating top-left overlay anchored inside the canvas container. Composition (in order):

- Save status pill — `aria-live="polite"` so screen readers announce changes. Colour-coded: emerald (saved), amber (saving), sky (unsaved), red (error). When `saveStatus === 'saved' && lastSavedAt`, the pill shows `"Saved HH:MM"`.
- Snap toggle checkbox
- Floor selector (only shown when `floors.length > 1`): `<select>` with `All Floors` plus each floor by name
- Object type picker + Add button — adds the chosen type to the currently selected floor
- Duplicate / Delete buttons — disabled when `selectedId` is null

The toolbar reaches into the store via individual `useCanvasStore` selectors to avoid re-rendering on unrelated state changes.

---

## Frontend: Project Page

New state and effects layered on the Sprint 5 page:

```typescript
const [prompt, setPrompt] = useState('')
const [generating, setGenerating] = useState(false)
const [generateError, setGenerateError] = useState<string | null>(null)
const [layoutSaving, setLayoutSaving] = useState(false)
const [layoutSaveError, setLayoutSaveError] = useState<string | null>(null)
const [versionName, setVersionName] = useState('')
const [changeSummary, setChangeSummary] = useState('')
const [hasSavedLayout, setHasSavedLayout] = useState(false)
const designId = useCanvasStore((s) => s.designId)
const loadLayout = useCanvasStore((s) => s.loadLayout)
const clearLayout = useCanvasStore((s) => s.clearLayout)
const serializeLayout = useCanvasStore((s) => s.serializeLayout)
```

### Mount

```ts
useEffect(() => {
  loadProject() // sets project state
  try {
    const latestDesign = await getLatestProjectDesign(projectId)
    loadLayout(latestDesign); setHasSavedLayout(true)
  } catch (err) {
    if (err.response?.status === 404) { clearLayout(); setHasSavedLayout(false) }
    else console.warn(...)
  }
}, [id, navigate, loadLayout])
```

### Generate

`generateLayout(prompt, id)` posts `projectId` so the layout is saved server-side. On success, the response (with `designId`/`designVersionId`) is loaded into the store.

### Save Layout

```ts
async function handleSaveLayout() {
  if (!designId) return
  setLayoutSaving(true)
  setLayoutSaveError(null)
  useCanvasStore.setState({ saveStatus: 'saving' })
  const thumbnailUrl = captureCanvasThumbnail()
  try {
    const result = await saveDesignLayout(designId, serializeLayout(), {
      versionName, changeSummary, thumbnailUrl,
    })
    loadLayout(result)
  } catch (err) {
    useCanvasStore.setState({ saveStatus: 'error' })
    setLayoutSaveError(err.response?.data?.error ?? 'Failed to save layout')
  } finally { setLayoutSaving(false) }
}
```

`captureCanvasThumbnail()` calls `document.querySelector('canvas').toDataURL('image/png')` inside a try/catch and returns `null` on failure (Sprint 6 keeps the call but the thumbnail field is only persisted once Sprint 7 ships).

### Empty state

When `!hasSavedLayout && rooms.length === 0`, the canvas area shows a pointer-transparent dashed pill: `"No saved layout yet. Generate a layout from the prompt below."`

---

## Testing

### Backend — `test_designs.py` (additions in Sprint 6)

1. `test_generate_design_returns_multi_floor_layout_and_logs_activity` — `"2 floor, 3 bedroom layout with kitchen, living room, bathroom"` returns 2 floors, includes Stairs, persists Design + DesignVersion(version_number=1), logs `design.generated`.
2. `test_generate_design_requires_auth` — 401 without Bearer token.
3. `test_latest_design_returns_saved_layout` — generation followed by `/latest` returns the same `designId` and rooms.
4. `test_save_design_updates_layout_and_creates_new_version` — `PUT /api/design/{id}` updates `layout_json`, creates `DesignVersion(version_number=2)`, logs `layout.saved`.

### Frontend — `canvasStore.test.ts` (additions in Sprint 6)

1. `updateRoom` patches position, size, rotation, and does not affect other rooms
2. Snap-to-grid rounds X/Z position to the nearest `gridSize`
3. `updateRoom` logs an `object.moved` activity entry and marks `saveStatus = 'unsaved'`
4. `deleteRoom` removes the room, clears the selection if it was selected, logs `object.deleted`
5. `duplicateRoom` creates a `"<label> Copy"`, selects the new room, preserves floor assignment
6. `addObject('wall')` inserts a wall with `OBJECT_DEFAULTS.wall`, selects it, logs `object.added`
7. `addObject` on selected floor places the new room at the right elevation (Y matches `elevation + h/2`)
8. `loadLayout` accepts multi-floor input and `selectedFloor` defaults to the first floor
9. `serializeLayout` returns rooms grouped under their floors with updated `totalFloors`

---

## Definition of Done

- [x] Alembic `004_create_designs.py` adds `designs` and `design_versions`
- [x] `POST /api/design/generate` with `projectId` persists Design + first DesignVersion
- [x] `GET /api/design/project/{id}/latest` returns the latest design or 404
- [x] `PUT /api/design/{id}` updates layout and appends a manual DesignVersion
- [x] `design.generated` and `layout.saved` ActivityLog entries
- [x] Multi-floor layouts (`floors[]`, Stairs aligned across floors, floor-aware room placement)
- [x] Canvas store supports object types, rotation, floors, snap, save status, in-memory activity log
- [x] Direct pointer drag (no TransformControls) with orbit toggle
- [x] Inspector: label, type, floor, position, size, rotation, duplicate, delete, recent edits
- [x] EditorToolbar: save pill, snap toggle, floor selector, add-object, duplicate, delete
- [x] Keyboard: Ctrl/Cmd+D duplicate, Delete/Backspace delete (suppressed in text fields)
- [x] Project page: loads latest design on mount, Save Layout button captures thumbnail (used by Sprint 7)
- [x] Empty state shown when there's no saved layout and no rooms
- [x] `npx tsc --noEmit` passes
- [x] Backend test suite passes including the four new design tests
