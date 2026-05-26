# Sprint 6: 3D Editing Workflow

## Goal

Users have a complete in-browser editing toolkit for the current generated layout: select, move, resize, rotate, duplicate, delete, snap to grid, add objects, see labels, and see edit/save feedback.

## Implemented

- Canvas store now tracks object type, rotation, snap-to-grid, save status, last saved time, and in-memory activity log entries.
- Inspector supports label editing, precise resize, precise rotation, duplicate, and delete.
- Canvas renders labels above objects.
- Transform drag movement respects snap-to-grid when enabled.
- Keyboard shortcuts:
  - Ctrl+D / Cmd+D duplicates the selected object.
  - Delete / Backspace removes the selected object.
- Editor toolbar supports save status, snap toggle, add object, duplicate, and delete.
- Add object supports room, wall, door, window, stair, floor, and open space.
- In-memory activity log records add, move, resize, rotate, rename, duplicate, and delete edits with old/new values.
- Debounced in-memory auto-save status shows Saving, then Saved after edits.
- Canvas store tests expanded from 9 to 16 tests.

## Deferred

- Persistent design save/load remains in Sprint 7.
- Persistent activity history/API remains in Sprint 9.
- Named versions and restore remain in Sprint 9.

## Verification

- `npm test` passes: 16 frontend tests.
- `npm run build` passes.
- Backend regression tests pass: 33 tests.
- Docker Compose stack runs:
  - Frontend: `http://localhost:5173`
  - Backend: `http://localhost:8000`
  - Project Postgres: `localhost:5433`
