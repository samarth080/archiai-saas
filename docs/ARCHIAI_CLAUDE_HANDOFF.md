# ArchiAI Continuation Handoff

Repository: `D:\Archi-AI\archiai-saas`
Current branch: `mvp/phase5-2d-svg-editor`

## Instructions Before Continuing

1. Read `AGENTS.md` and `CLAUDE.md` completely.
2. Inspect `git status` and recent commits.
3. Do not switch branches, merge, push, or modify files immediately.
4. First report your understanding and the current workflow status.
5. Work step by step, continuously update the todo list, and commit every completed checkpoint separately.

## Product Architecture

ArchiAI is not an LLM layout generator.

```text
Natural-language prompt
  -> local Qwen extracts structured requirements
  -> deterministic ProgramGraph and layout engines
  -> scoring and validation
  -> editable Plan and 3D canvas
```

The current local runtime is Qwen through LM Studio, not Ollama. The LLM only interprets language; layout geometry remains deterministic.

## Current Workflow Progress

Phases 0-5 are substantially complete:

- Phase 0: environment and contracts
- Phase 1: deterministic engine and hard validator
- Phase 2: local LLM structured extraction
- Phase 3: clarification and defaults
- Phase 4: API and database integration
- Phase 5: shared-state SVG Plan editor and visible refinement playback

The next planned phase after user review is:

- Phase 6: canonical quality scoring and Vastu feedback

Do not begin Phase 6 until explicitly approved by the user.

## Recently Completed Work

### Local LLM

- Model: `qwen/qwen3.5-9b`
- Context length: 4096
- Parallel requests: 1
- An exact long prompt completed through Docker in approximately 14.9 seconds.
- The backend accesses LM Studio through `host.docker.internal:1234/v1`.

Relevant commit:

- `85b935d fix(mvp): harden local LLM extraction flow`

### Canvas Fixes

- Removed duplicated generated partition walls from Plan view.
- Consolidated the previous 2D and Plan controls into one Plan mode.
- Removed the enormous native SVG focus ring.
- Moved the Tape panel below the project header.
- Introduced an architectural blue-gray workspace and warm drawing-sheet palette.

Relevant commits:

- `6abeafe fix(canvas): avoid duplicate partition walls in plan views`
- `519d337 fix(canvas): unify plan mode and tame selection focus`
- `2f8fd1d fix(canvas): keep measurements clear of project header`
- `2c8d2d3 feat(canvas): introduce architectural workspace palette`

A stale Vite module-cache problem was previously found. Restarting the frontend container fixed it. If the old UI returns, verify the JavaScript served by port 5173 before modifying source again.

### Visible Refinement Playback

The previous Refine flow replaced the entire layout instantly. It now:

1. Receives authoritative ordered changes from the backend.
2. Shows an **Applying refinement** progress card.
3. Focuses the affected floor and object.
4. Applies resize, remove, and add operations visibly.
5. Loads the exact final server-saved layout.
6. Creates only one backend `DesignVersion`.
7. Creates no artificial undo entries, drafts, or additional versions during playback.

The backend response now additively includes:

```text
refinementChanges[]:
  - action
  - objectId
  - roomType
  - label
  - floorLevel
  - description
```

Relevant commits:

- `da46388 feat(refine): expose ordered object changes`
- `d9b5fc2 feat(refine): play changes on the canvas`

Current refinement limitations:

- Supports add, remove, and resize.
- Does not support move, rotate, adjacency changes, or intelligent repacking.
- Added rooms use append-only placement.
- Resizing can potentially create overlaps.

Manual refinement test:

```text
Make the kitchen bigger, remove the utility room, and add a study.
```

Expected playback order:

1. Resize Kitchen
2. Remove Utility
3. Add Study

## Latest Verification

Frontend commands:

```powershell
cd frontend
npm test
npm run build
```

Results:

- 35 test files passed.
- 197 frontend tests passed.
- Production build passed.

Backend command:

```powershell
.\.venv311\Scripts\python.exe -m pytest backend/app/tests -q
```

Results:

- 650 backend tests passed.
- 3 tests skipped.
- 1 dependency deprecation warning.

## Working-Tree Safety

The following were pre-existing or user-owned changes and must not be included in unrelated commits:

- `CLAUDE.md`
- `README.md`
- `backend/Dockerfile`
- `.thumbnail`
- `AGENTS.md`
- `debug_renders/`
- `screenshots/`
- `uploads/`

Verify the current working tree instead of assuming this list is unchanged.

## User Working Preferences

- Proceed one focused step at a time.
- Explain the reasoning behind each change.
- Keep the todo list visibly updated.
- Commit every completed change.
- Do not push unless explicitly requested.
- Avoid unrelated refactoring.
- Stop after each requested phase for manual review.

## Immediate Continuation Point

The current task is user testing and review of Phase 5 and visible refinement playback. Do not begin Phase 6 automatically. First inspect the repository, confirm the state above against code and tests, and wait for explicit approval to continue.
