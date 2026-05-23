# Sprint 4 — Basic 3D Canvas: Design Spec

**Date:** 2026-05-24
**Status:** Approved
**Sprint Goal:** Replace the canvas placeholder in the Project workspace with a real interactive 3D scene — users can view, select, move, and inspect hardcoded room blocks using mouse controls.

---

## Context

Builds on Sprint 3 (Project workspace page with 🏗️ placeholder). The following already exist and must not be changed except where noted:

- `src/store/authStore.ts` — Zustand auth store
- `src/services/project.service.ts` — Project CRUD service
- `src/pages/Dashboard/index.tsx` — dashboard with sidebar (MODIFY: extract sidebar)
- `src/pages/Project/index.tsx` — project workspace with placeholder (MODIFY: replace placeholder, extract sidebar)
- `src/App.tsx` — routing, no changes needed
- `src/components/ui/Button.tsx`, `src/components/ui/Input.tsx` — no changes

No backend changes in this sprint. Canvas state is in-memory only — it resets on page reload. Persistence is Sprint 7.

---

## New Packages

```bash
npm install three @react-three/fiber @react-three/drei
npm install -D @types/three
```

---

## Architecture

Two concerns added on top of the existing frontend:

1. **Shared Sidebar component** (`src/components/layout/Sidebar.tsx`) — extracted from the duplicated sidebar code in Dashboard and Project pages. Both pages are updated to use it.

2. **Canvas subsystem** — a Zustand store for canvas state, a set of focused R3F components, and updates to the Project page to mount the canvas and inspector.

The Project workspace page content area becomes:
```
┌─────────────────────────────────────┬───────────────┐
│  R3F Canvas (flex-1)                │  Inspector    │
│  - Scene: lights, grid              │  (200px)      │
│  - RoomMesh × N (colored boxes)     │  visible when │
│  - TransformHandler (selected only) │  room is      │
│  - OrbitControls                    │  selected     │
└─────────────────────────────────────┴───────────────┘
```

State flows through `canvasStore` — both the R3F canvas and the React inspector panel read and write from the same store.

---

## File Map

```
frontend/src/
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx              CREATE (extracted from Dashboard + Project)
│   └── canvas/
│       ├── Canvas3D.tsx             CREATE — R3F Canvas wrapper
│       ├── Scene.tsx                CREATE — lights, grid, OrbitControls
│       ├── RoomMesh.tsx             CREATE — single colored box with selection highlight
│       ├── TransformHandler.tsx     CREATE — TransformControls + OrbitControls sync
│       └── Inspector.tsx            CREATE — fixed right panel, position/size fields
├── store/
│   └── canvasStore.ts               CREATE — rooms array, selectedId, actions
└── pages/
    ├── Dashboard/index.tsx          MODIFY — use <Sidebar />
    └── Project/index.tsx            MODIFY — use <Sidebar />, mount canvas + inspector
```

---

## Canvas Store (`src/store/canvasStore.ts`)

```typescript
import { create } from 'zustand'

export interface Room {
  id: string
  label: string
  position: { x: number; y: number; z: number }
  size: { w: number; h: number; d: number }
  color: string
}

interface CanvasState {
  rooms: Room[]
  selectedId: string | null
  selectRoom: (id: string) => void
  deselectAll: () => void
  updateRoom: (id: string, patch: Partial<Omit<Room, 'id'>>) => void
  deleteRoom: (id: string) => void
}

export const useCanvasStore = create<CanvasState>((set) => ({
  rooms: INITIAL_ROOMS,
  selectedId: null,
  selectRoom: (id) => set({ selectedId: id }),
  deselectAll: () => set({ selectedId: null }),
  updateRoom: (id, patch) =>
    set((state) => ({
      rooms: state.rooms.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    })),
}))
```

### Initial hardcoded scene

Five rooms representing a basic apartment, spaced on a flat grid (Y=0):

| id | label | position | size (w×h×d) | color |
|---|---|---|---|---|
| `room-1` | Living Room | (0, 0, 0) | 6×3×5 | `#818cf8` (indigo-400) |
| `room-2` | Kitchen | (7, 0, 0) | 4×3×4 | `#34d399` (emerald-400) |
| `room-3` | Master Bedroom | (0, 0, 6) | 5×3×5 | `#fb923c` (orange-400) |
| `room-4` | Bedroom | (6, 0, 6) | 4×3×4 | `#f472b6` (pink-400) |
| `room-5` | Bathroom | (11, 0, 6) | 3×3×3 | `#60a5fa` (blue-400) |

---

## Shared Sidebar (`src/components/layout/Sidebar.tsx`)

Extracted verbatim from the current Dashboard and Project pages. Props:

```typescript
interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
}
```

Renders: ArchiAI wordmark, "📁 Projects" nav item (always active for now), user name + logout button. Both Dashboard and Project pages import and use `<Sidebar>`.

---

## Canvas Components

### `Canvas3D.tsx`

R3F `<Canvas>` wrapper. Sets camera initial position at `(10, 12, 10)` looking at origin. Composes `<Scene />`, one `<RoomMesh />` per room, and `<TransformHandler />`. Handles canvas background click to deselect: `onClick` on the canvas root calls `deselectAll()` (rooms stop propagation on their own click).

```typescript
interface Canvas3DProps {
  className?: string
}
```

### `Scene.tsx`

No props. Renders inside R3F context:
- `<ambientLight intensity={0.5} />`
- `<directionalLight position={[10, 20, 10]} intensity={1} castShadow />`
- `<gridHelper args={[40, 40, '#94a3b8', '#e2e8f0']} />`
- `<OrbitControls ref={orbitRef} />` — `orbitRef` is passed via context or module-level ref so `TransformHandler` can disable it while dragging

### `RoomMesh.tsx`

Props:
```typescript
interface RoomMeshProps {
  room: Room
}
```

Renders a `<mesh>` with `<boxGeometry>` sized to `room.size` at `room.position`. Material: `<meshStandardMaterial color={room.color} emissive={isSelected ? '#ffffff' : '#000000'} emissiveIntensity={isSelected ? 0.15 : 0} />`. Reads `selectedId` from store. `onClick` (with `stopPropagation`) calls `selectRoom(room.id)`.

### `TransformHandler.tsx`

No props. Reads `selectedId` and the selected room from store. When `selectedId` is non-null, renders `<TransformControls>` (mode `"translate"`) attached to the selected mesh object. On `onMouseDown` disables OrbitControls; on `onMouseUp` re-enables. On `onChange` reads the mesh's updated position and calls `updateRoom(selectedId, { position: { x, y, z } })` keeping Y at 0 (rooms stay flat on the grid).

### `Inspector.tsx`

No props. Reads `selectedId` and selected room from store. Renders as a fixed `200px` wide right panel (`bg-white border-l border-gray-200`). Only visible when `selectedId` is non-null.

Content:
- Room label at top (read-only `<span>`)
- **Position** section: three number `<input>` fields for X, Y, Z — Y field is disabled (always 0)
- **Size** section: three number `<input>` fields for W (width), H (height), D (depth) — min value 1
- Each field: `onChange` calls `updateRoom(selectedId, { position/size: ... })`
- **Delete** button (`bg-red-500 text-white`) — calls `updateRoom`... actually calls a `deleteRoom` action and `deselectAll()`

Wait — the store needs a `deleteRoom` action. Add to store:
```typescript
deleteRoom: (id: string) => void
```

- **Delete** button → `deleteRoom(selectedId)` → `deselectAll()`

---

## Project Page Updates (`src/pages/Project/index.tsx`)

- Import and use `<Sidebar>` instead of inline sidebar JSX
- Replace the canvas placeholder div:

```tsx
{/* Before */}
<div className="flex-1 bg-gray-100 flex items-center justify-center flex-col gap-2">
  <span className="text-4xl">🏗️</span>
  <p className="text-gray-400 text-sm">3D canvas coming in Sprint 4</p>
</div>

{/* After */}
<div className="flex-1 flex overflow-hidden">
  <Canvas3D className="flex-1 h-full" />
  <Inspector />
</div>
```

The Inspector renders nothing when no room is selected (no panel shown, canvas takes full width).

---

## Dashboard Page Updates (`src/pages/Dashboard/index.tsx`)

- Import and use `<Sidebar>` instead of inline sidebar JSX
- No other changes

---

## Error Handling

| Scenario | Behaviour |
|---|---|
| Three.js/WebGL not supported | R3F shows a fallback message automatically |
| Room not found in store on inspector edit | Guard with `if (!room) return` — no crash |
| TransformControls fires on unmounted component | Cleanup ref in useEffect return |

---

## Definition of Done (Sprint 4)

- [ ] Shared `<Sidebar>` component extracted; Dashboard and Project pages use it
- [ ] `three`, `@react-three/fiber`, `@react-three/drei`, `@types/three` installed
- [ ] R3F canvas renders in the Project workspace with correct lighting and grid
- [ ] Camera orbits, zooms, and pans with mouse (OrbitControls)
- [ ] 5 hardcoded room boxes visible, each a different color
- [ ] Clicking a room selects it (emissive highlight) and opens the Inspector panel
- [ ] Clicking empty canvas deselects (Inspector closes)
- [ ] TransformControls gizmo appears on selected room; dragging it moves the room
- [ ] OrbitControls disabled while TransformControls is active (no camera fighting)
- [ ] Inspector X/Y/Z fields update when room is moved via gizmo
- [ ] Editing an inspector field moves the room in the canvas
- [ ] Delete button in inspector removes the room from the scene
- [ ] `npx tsc --noEmit` passes with zero errors
- [ ] `docker-compose up` serves the working canvas
