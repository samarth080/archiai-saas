# Sprint 4 — Basic 3D Canvas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 🏗️ placeholder in the Project workspace with a real interactive Three.js canvas — users can orbit the camera, click room blocks to select them, drag a transform gizmo to move them, and edit position/size in a fixed inspector panel.

**Architecture:** Zustand store (`canvasStore`) holds rooms and selection state, shared between R3F canvas components (which render/move meshes) and the React inspector panel (which shows and edits values). OrbitControls ref is created in `Canvas3D` and passed as a prop to both `Scene` (which mounts OrbitControls) and each `RoomMesh` (which disables/enables orbit during TransformControls drag). TransformControls wraps the selected room mesh directly inside `RoomMesh`.

**Tech Stack:** React 18, TypeScript, Vite, Tailwind CSS, Zustand, `three`, `@react-three/fiber`, `@react-three/drei`, Vitest (for store tests)

---

## File Map

```
frontend/src/
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx              CREATE — extracted from Dashboard + Project pages
│   └── canvas/
│       ├── Canvas3D.tsx             CREATE — R3F <Canvas> wrapper, passes orbitRef down
│       ├── Scene.tsx                CREATE — lights, grid, OrbitControls, deselect plane
│       ├── RoomMesh.tsx             CREATE — colored box, selection highlight, TransformControls
│       └── Inspector.tsx            CREATE — fixed 200px right panel, position/size fields
├── store/
│   └── canvasStore.ts               CREATE — rooms[], selectedId, selectRoom/deselectAll/updateRoom/deleteRoom
├── store/
│   └── canvasStore.test.ts          CREATE — Vitest tests for store actions
└── pages/
    ├── Dashboard/index.tsx          MODIFY — replace inline <aside> with <Sidebar />
    └── Project/index.tsx            MODIFY — replace inline <aside> and placeholder with <Sidebar />, <Canvas3D />, <Inspector />
```

---

## Task 1: Extract Shared Sidebar Component

**Files:**
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Modify: `frontend/src/pages/Dashboard/index.tsx`
- Modify: `frontend/src/pages/Project/index.tsx`

- [ ] **Step 1: Create `frontend/src/components/layout/Sidebar.tsx`**

```tsx
import { Button } from '../ui/Button'

interface SidebarProps {
  userName?: string
  userEmail?: string
  onLogout: () => void
}

export function Sidebar({ userName, userEmail, onLogout }: SidebarProps) {
  return (
    <aside className="w-52 flex-shrink-0 bg-slate-800 text-white flex flex-col">
      <div className="p-4 border-b border-slate-700">
        <span className="font-bold text-lg">ArchiAI</span>
      </div>
      <nav className="flex-1 p-3">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-slate-700 text-sm font-medium">
          <span>📁</span>
          <span>Projects</span>
        </div>
      </nav>
      <div className="p-4 border-t border-slate-700">
        <p className="text-sm text-slate-300 truncate mb-2">
          {userName ?? userEmail ?? ''}
        </p>
        <Button variant="secondary" onClick={onLogout} className="w-full text-sm">
          Logout
        </Button>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Update `frontend/src/pages/Dashboard/index.tsx` to use `<Sidebar />`**

Replace the entire `{/* Sidebar */}` block (lines 33–50) with:

```tsx
import { Sidebar } from '../../components/layout/Sidebar'
// (add this import at the top)
```

And replace the `<aside>...</aside>` JSX with:

```tsx
<Sidebar
  userName={user?.name}
  userEmail={user?.email}
  onLogout={logOut}
/>
```

Remove `const { logOut, user } = useAuth()` only if `logOut` and `user` are no longer used elsewhere in the file — they are still used to pass to `<Sidebar />`, so keep the destructuring.

- [ ] **Step 3: Update `frontend/src/pages/Project/index.tsx` to use `<Sidebar />`**

Add the import at the top:

```tsx
import { Sidebar } from '../../components/layout/Sidebar'
```

Replace the `{/* Sidebar */}` block (lines 109–126) with:

```tsx
<Sidebar
  userName={user?.name}
  userEmail={user?.email}
  onLogout={logOut}
/>
```

- [ ] **Step 4: Run TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors. If `logOut` or `user` are now unused, remove them from the `useAuth()` destructure.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/Sidebar.tsx \
        frontend/src/pages/Dashboard/index.tsx \
        frontend/src/pages/Project/index.tsx
git commit -m "refactor(sprint4): extract shared Sidebar component"
```

---

## Task 2: Install Packages, Set Up Vitest, Create Canvas Store

**Files:**
- Modify: `frontend/package.json` (via npm install)
- Create: `frontend/src/store/canvasStore.ts`
- Create: `frontend/src/store/canvasStore.test.ts`

- [ ] **Step 1: Install runtime packages**

```bash
cd /path/to/worktree/frontend
npm install three @react-three/fiber @react-three/drei
```

Expected: packages added to `dependencies` in `package.json`.

- [ ] **Step 2: Install dev packages**

```bash
npm install -D @types/three vitest
```

Expected: `@types/three` and `vitest` added to `devDependencies`.

- [ ] **Step 3: Add test script to `package.json`**

Open `frontend/package.json`. In the `"scripts"` section, add:

```json
"test": "vitest run"
```

Full scripts section should look like:

```json
"scripts": {
  "dev": "vite",
  "build": "tsc && vite build",
  "preview": "vite preview",
  "test": "vitest run"
}
```

- [ ] **Step 4: Create `frontend/src/store/canvasStore.ts`**

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

export const INITIAL_ROOMS: Room[] = [
  {
    id: 'room-1',
    label: 'Living Room',
    position: { x: 0, y: 1.5, z: 0 },
    size: { w: 6, h: 3, d: 5 },
    color: '#818cf8',
  },
  {
    id: 'room-2',
    label: 'Kitchen',
    position: { x: 7, y: 1.5, z: 0 },
    size: { w: 4, h: 3, d: 4 },
    color: '#34d399',
  },
  {
    id: 'room-3',
    label: 'Master Bedroom',
    position: { x: 0, y: 1.5, z: 6 },
    size: { w: 5, h: 3, d: 5 },
    color: '#fb923c',
  },
  {
    id: 'room-4',
    label: 'Bedroom',
    position: { x: 6, y: 1.5, z: 6 },
    size: { w: 4, h: 3, d: 4 },
    color: '#f472b6',
  },
  {
    id: 'room-5',
    label: 'Bathroom',
    position: { x: 11, y: 1.5, z: 6 },
    size: { w: 3, h: 3, d: 3 },
    color: '#60a5fa',
  },
]

export const useCanvasStore = create<CanvasState>((set) => ({
  rooms: INITIAL_ROOMS,
  selectedId: null,
  selectRoom: (id) => set({ selectedId: id }),
  deselectAll: () => set({ selectedId: null }),
  updateRoom: (id, patch) =>
    set((state) => ({
      rooms: state.rooms.map((r) => (r.id === id ? { ...r, ...patch } : r)),
    })),
  deleteRoom: (id) =>
    set((state) => ({
      rooms: state.rooms.filter((r) => r.id !== id),
    })),
}))
```

Note: all rooms have `position.y = h/2` so their bottom sits exactly on the grid at Y=0. Mesh position equals the store position directly — no offset needed.

- [ ] **Step 5: Write `frontend/src/store/canvasStore.test.ts`**

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { useCanvasStore, INITIAL_ROOMS } from './canvasStore'

beforeEach(() => {
  useCanvasStore.setState({
    rooms: INITIAL_ROOMS.map((r) => ({ ...r, position: { ...r.position } })),
    selectedId: null,
  })
})

describe('selectRoom', () => {
  it('sets selectedId', () => {
    useCanvasStore.getState().selectRoom('room-1')
    expect(useCanvasStore.getState().selectedId).toBe('room-1')
  })

  it('overwrites a previous selection', () => {
    useCanvasStore.getState().selectRoom('room-1')
    useCanvasStore.getState().selectRoom('room-2')
    expect(useCanvasStore.getState().selectedId).toBe('room-2')
  })
})

describe('deselectAll', () => {
  it('clears selectedId', () => {
    useCanvasStore.getState().selectRoom('room-1')
    useCanvasStore.getState().deselectAll()
    expect(useCanvasStore.getState().selectedId).toBeNull()
  })
})

describe('updateRoom', () => {
  it('patches position of the target room', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 10, y: 1.5, z: 10 },
    })
    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.position).toEqual({ x: 10, y: 1.5, z: 10 })
  })

  it('does not affect other rooms', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      position: { x: 10, y: 1.5, z: 10 },
    })
    const room2 = useCanvasStore.getState().rooms.find((r) => r.id === 'room-2')
    expect(room2?.position).toEqual({ x: 7, y: 1.5, z: 0 })
  })

  it('patches size independently of position', () => {
    useCanvasStore.getState().updateRoom('room-1', {
      size: { w: 8, h: 3, d: 6 },
    })
    const room = useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')
    expect(room?.size).toEqual({ w: 8, h: 3, d: 6 })
    expect(room?.position).toEqual({ x: 0, y: 1.5, z: 0 })
  })
})

describe('deleteRoom', () => {
  it('removes the room with the given id', () => {
    useCanvasStore.getState().deleteRoom('room-1')
    expect(useCanvasStore.getState().rooms.find((r) => r.id === 'room-1')).toBeUndefined()
  })

  it('does not remove other rooms', () => {
    useCanvasStore.getState().deleteRoom('room-1')
    expect(useCanvasStore.getState().rooms).toHaveLength(4)
  })
})
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd /path/to/worktree/frontend && npm test
```

Expected output:
```
✓ canvasStore.test.ts (8)
  ✓ selectRoom > sets selectedId
  ✓ selectRoom > overwrites a previous selection
  ✓ deselectAll > clears selectedId
  ✓ updateRoom > patches position of the target room
  ✓ updateRoom > does not affect other rooms
  ✓ updateRoom > patches size independently of position
  ✓ deleteRoom > removes the room with the given id
  ✓ deleteRoom > does not remove other rooms

Test Files  1 passed (1)
Tests       8 passed (8)
```

- [ ] **Step 7: TypeScript check**

```bash
npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/package-lock.json \
        frontend/src/store/canvasStore.ts \
        frontend/src/store/canvasStore.test.ts
git commit -m "feat(sprint4): add canvas store with room state and vitest tests"
```

---

## Task 3: Scene Component

**Files:**
- Create: `frontend/src/components/canvas/Scene.tsx`

This component renders inside the R3F `<Canvas>` context. It adds lighting, a grid, and OrbitControls (with a forwarded ref). It also adds an invisible plane to catch empty-area clicks for deselection.

- [ ] **Step 1: Create `frontend/src/components/canvas/Scene.tsx`**

```tsx
import { useRef } from 'react'
import { OrbitControls, Grid } from '@react-three/drei'
import { useCanvasStore } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface SceneProps {
  orbitRef: React.RefObject<OrbitHandle>
}

export function Scene({ orbitRef }: SceneProps) {
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 20, 10]} intensity={1} castShadow />

      {/* Grid on the floor plane */}
      <Grid
        args={[40, 40]}
        position={[0, 0, 0]}
        cellColor="#94a3b8"
        sectionColor="#e2e8f0"
        fadeDistance={60}
        infiniteGrid
      />

      {/* OrbitControls — ref exposed so RoomMesh can disable during drag */}
      <OrbitControls ref={orbitRef as React.RefObject<any>} makeDefault />

      {/* Invisible plane — catches clicks on empty canvas to deselect */}
      <mesh
        rotation={[-Math.PI / 2, 0, 0]}
        position={[0, -0.01, 0]}
        onClick={() => deselectAll()}
      >
        <planeGeometry args={[200, 200]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
    </>
  )
}
```

Note: `orbitRef as React.RefObject<any>` is needed because drei's `OrbitControls` ref type and our minimal `OrbitHandle` interface don't share a declared subtype relationship. The cast is safe — drei's OrbitControls instance does have an `enabled` property.

- [ ] **Step 2: TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/canvas/Scene.tsx
git commit -m "feat(sprint4): add Scene component with lighting, grid, and OrbitControls"
```

---

## Task 4: RoomMesh Component

**Files:**
- Create: `frontend/src/components/canvas/RoomMesh.tsx`

This renders one room box. When selected, it wraps in `TransformControls` for dragging and disables OrbitControls while the user drags. The position stored in the Zustand store equals the Three.js mesh center position (Y = h/2, so the box bottom sits on the grid).

- [ ] **Step 1: Create `frontend/src/components/canvas/RoomMesh.tsx`**

```tsx
import { useRef } from 'react'
import { TransformControls } from '@react-three/drei'
import type { ThreeEvent } from '@react-three/fiber'
import * as THREE from 'three'
import { useCanvasStore, Room } from '../../store/canvasStore'

interface OrbitHandle {
  enabled: boolean
}

interface RoomMeshProps {
  room: Room
  orbitRef: React.RefObject<OrbitHandle>
}

export function RoomMesh({ room, orbitRef }: RoomMeshProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const selectedId = useCanvasStore((s) => s.selectedId)
  const selectRoom = useCanvasStore((s) => s.selectRoom)
  const updateRoom = useCanvasStore((s) => s.updateRoom)

  const isSelected = selectedId === room.id

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation()
    selectRoom(room.id)
  }

  const handleTransformMouseDown = () => {
    if (orbitRef.current) orbitRef.current.enabled = false
  }

  const handleTransformMouseUp = () => {
    if (orbitRef.current) orbitRef.current.enabled = true
  }

  const handleTransformChange = () => {
    if (meshRef.current) {
      const pos = meshRef.current.position
      updateRoom(room.id, {
        position: { x: pos.x, y: pos.y, z: pos.z },
      })
    }
  }

  const mesh = (
    <mesh
      ref={meshRef}
      position={[room.position.x, room.position.y, room.position.z]}
      onClick={handleClick}
    >
      <boxGeometry args={[room.size.w, room.size.h, room.size.d]} />
      <meshStandardMaterial
        color={room.color}
        emissive={isSelected ? '#ffffff' : '#000000'}
        emissiveIntensity={isSelected ? 0.15 : 0}
      />
    </mesh>
  )

  if (isSelected) {
    return (
      <TransformControls
        mode="translate"
        onMouseDown={handleTransformMouseDown}
        onMouseUp={handleTransformMouseUp}
        onChange={handleTransformChange}
      >
        {mesh}
      </TransformControls>
    )
  }

  return mesh
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/canvas/RoomMesh.tsx
git commit -m "feat(sprint4): add RoomMesh with selection highlight and TransformControls"
```

---

## Task 5: Inspector Component

**Files:**
- Create: `frontend/src/components/canvas/Inspector.tsx`

Fixed 200px right panel. Visible only when a room is selected. Position and size fields each call `updateRoom` on change. Delete button calls `deleteRoom` then `deselectAll`.

- [ ] **Step 1: Create `frontend/src/components/canvas/Inspector.tsx`**

```tsx
import { useCanvasStore } from '../../store/canvasStore'

export function Inspector() {
  const selectedId = useCanvasStore((s) => s.selectedId)
  const rooms = useCanvasStore((s) => s.rooms)
  const updateRoom = useCanvasStore((s) => s.updateRoom)
  const deleteRoom = useCanvasStore((s) => s.deleteRoom)
  const deselectAll = useCanvasStore((s) => s.deselectAll)

  const room = rooms.find((r) => r.id === selectedId)

  if (!room) return null

  const inputClass =
    'w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400 disabled:bg-gray-50 disabled:text-gray-400'

  const handlePositionChange = (axis: 'x' | 'y' | 'z', value: string) => {
    const num = parseFloat(value)
    if (isNaN(num)) return
    updateRoom(room.id, {
      position: { ...room.position, [axis]: num },
    })
  }

  const handleSizeChange = (dim: 'w' | 'h' | 'd', value: string) => {
    const num = parseFloat(value)
    if (isNaN(num) || num < 1) return
    updateRoom(room.id, {
      size: { ...room.size, [dim]: num },
    })
  }

  const handleDelete = () => {
    deleteRoom(room.id)
    deselectAll()
  }

  return (
    <div className="w-48 flex-shrink-0 bg-white border-l border-gray-200 flex flex-col p-4 overflow-y-auto">
      <h2 className="font-semibold text-gray-900 text-sm truncate mb-4">{room.label}</h2>

      <section className="mb-4">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Position</p>
        <div className="space-y-2">
          {(['x', 'y', 'z'] as const).map((axis) => (
            <div key={axis} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-3 uppercase">{axis}</span>
              <input
                type="number"
                className={inputClass}
                value={room.position[axis]}
                disabled={axis === 'y'}
                step={0.5}
                onChange={(e) => handlePositionChange(axis, e.target.value)}
              />
            </div>
          ))}
        </div>
      </section>

      <section className="mb-6">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Size</p>
        <div className="space-y-2">
          {([['w', 'Width'], ['h', 'Height'], ['d', 'Depth']] as const).map(([dim, label]) => (
            <div key={dim} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-8">{label[0]}</span>
              <input
                type="number"
                className={inputClass}
                value={room.size[dim]}
                min={1}
                step={0.5}
                onChange={(e) => handleSizeChange(dim, e.target.value)}
              />
            </div>
          ))}
        </div>
      </section>

      <button
        onClick={handleDelete}
        className="w-full bg-red-500 hover:bg-red-600 text-white text-xs font-medium py-2 rounded transition-colors"
      >
        Delete Room
      </button>
    </div>
  )
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/canvas/Inspector.tsx
git commit -m "feat(sprint4): add Inspector panel with position/size fields and delete"
```

---

## Task 6: Canvas3D Wrapper

**Files:**
- Create: `frontend/src/components/canvas/Canvas3D.tsx`

Composes `Scene`, all `RoomMesh` instances, provides the OrbitControls ref. The outer `<div>` handles canvas-level styling.

- [ ] **Step 1: Create `frontend/src/components/canvas/Canvas3D.tsx`**

```tsx
import { useRef } from 'react'
import { Canvas } from '@react-three/fiber'
import { useCanvasStore } from '../../store/canvasStore'
import { Scene } from './Scene'
import { RoomMesh } from './RoomMesh'

interface OrbitHandle {
  enabled: boolean
}

interface Canvas3DProps {
  className?: string
}

export function Canvas3D({ className = '' }: Canvas3DProps) {
  const orbitRef = useRef<OrbitHandle>(null)
  const rooms = useCanvasStore((s) => s.rooms)

  return (
    <div className={className}>
      <Canvas
        camera={{ position: [10, 12, 10], fov: 50 }}
        shadows
        style={{ width: '100%', height: '100%' }}
      >
        <Scene orbitRef={orbitRef} />
        {rooms.map((room) => (
          <RoomMesh key={room.id} room={room} orbitRef={orbitRef} />
        ))}
      </Canvas>
    </div>
  )
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/canvas/Canvas3D.tsx
git commit -m "feat(sprint4): add Canvas3D wrapper composing scene and room meshes"
```

---

## Task 7: Update Project Page — Replace Placeholder

**Files:**
- Modify: `frontend/src/pages/Project/index.tsx`

Replace the `{/* Canvas placeholder */}` div with `<Canvas3D>` and `<Inspector>`, and confirm `<Sidebar>` is already in use from Task 1.

- [ ] **Step 1: Add imports to `frontend/src/pages/Project/index.tsx`**

At the top of the file, add:

```tsx
import { Canvas3D } from '../../components/canvas/Canvas3D'
import { Inspector } from '../../components/canvas/Inspector'
```

- [ ] **Step 2: Replace the canvas placeholder div**

Find this block (around line 192–195):

```tsx
{/* Canvas placeholder */}
<div className="flex-1 bg-gray-100 flex items-center justify-center flex-col gap-2">
  <span className="text-4xl">🏗️</span>
  <p className="text-gray-400 text-sm">3D canvas coming in Sprint 4</p>
</div>
```

Replace with:

```tsx
{/* 3D Canvas + Inspector */}
<div className="flex-1 flex overflow-hidden">
  <Canvas3D className="flex-1 h-full" />
  <Inspector />
</div>
```

- [ ] **Step 3: Verify `<main>` has `overflow-hidden`**

The outer `<main>` tag should have `className="flex-1 flex flex-col overflow-hidden"`. If it currently says `overflow-y-auto`, change it to `overflow-hidden` — the canvas div manages its own sizing and the main area must not scroll.

- [ ] **Step 4: Run TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 5: Run tests**

```bash
npm test
```

Expected: 8 tests passing.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/Project/index.tsx
git commit -m "feat(sprint4): replace canvas placeholder with Canvas3D and Inspector"
```

---

## Task 8: Final Verification and CLAUDE.md Update

**Files:**
- Modify: `CLAUDE.md` (project root)

- [ ] **Step 1: Final TypeScript check**

```bash
cd /path/to/worktree/frontend && npx tsc --noEmit
```

Expected: zero errors.

- [ ] **Step 2: Final test run**

```bash
npm test
```

Expected: 8 tests, 0 failures.

- [ ] **Step 3: Mark Sprint 4 complete in `CLAUDE.md`**

Find the Sprint 4 line:

```markdown
### Sprint 4 — Basic 3D Canvas ⏳ Not Started
```

Replace with:

```markdown
### Sprint 4 — Basic 3D Canvas ✅ Complete
- [x] Shared `<Sidebar>` component extracted; Dashboard and Project pages use it
- [x] `three`, `@react-three/fiber`, `@react-three/drei`, `@types/three` installed
- [x] Vitest set up; 8 canvas store tests passing
- [x] R3F canvas renders in Project workspace with ambient/directional lighting and grid
- [x] Camera orbits, zooms, and pans with mouse (OrbitControls)
- [x] 5 hardcoded room boxes visible, each a different color
- [x] Clicking a room selects it (emissive highlight) and opens the Inspector panel
- [x] Clicking empty canvas deselects (Inspector closes)
- [x] TransformControls gizmo on selected room; dragging moves the room
- [x] OrbitControls disabled while TransformControls is active
- [x] Inspector X/Y/Z fields update when room is moved via gizmo
- [x] Editing an inspector field moves the room in the canvas
- [x] Delete button removes the room from the scene
- [x] `npx tsc --noEmit` passes with zero errors
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: mark Sprint 4 complete in CLAUDE.md"
```
