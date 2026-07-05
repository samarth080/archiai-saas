# ArchiAI TODO Return Checklist

Use this file when returning to the project after a pause. It rolls up the live TODOs from `CLAUDE.md` and `docs/SPRINT20_REMAINING_WORK.md`, then gives a repeatable checklist for picking work back up safely.

This file intentionally does not treat unchecked boxes inside old sprint specs/plans as live work unless the same item is also reflected in `CLAUDE.md` or the Sprint 20 remaining-work note. Many old spec checkboxes are historical implementation plans that have since been completed.

## Before Starting Any TODO

- [ ] Confirm the current branch with `git status --short --branch`.
- [ ] Check for unrelated untracked or dirty files and leave them alone unless they are part of the task.
- [ ] Read the relevant current section in `CLAUDE.md`.
- [ ] Read this checklist section for the chosen TODO.
- [ ] Create or switch to the right feature branch.
- [ ] Run the narrow baseline tests for the area you will touch.
- [ ] Add or update tests before/alongside the fix.
- [ ] Run focused checks after implementation.
- [ ] Run the full required checks before marking the TODO done.
- [ ] Update `CLAUDE.md` and this checklist when a TODO is completed, deferred, or superseded.
- [ ] Commit locally with a clear message.
- [ ] Do not push or open a PR unless explicitly asked.

## Priority 0 - Sprint 20 Closure

- [ ] Run the full live browser acceptance flow with backend and frontend servers running.
- [ ] Log in through the UI and open an editable project layout.
- [ ] Make several canvas edits and confirm the editor remains responsive.
- [ ] Simulate an expired access token during active editing.
- [ ] Trigger auto-save and confirm refresh happens without redirecting to login.
- [ ] Trigger manual Save Layout and confirm the save completes once.
- [ ] Confirm only one intended named version exists after manual save.
- [ ] Force refresh-token failure and confirm the app logs out safely.
- [ ] Confirm unsaved in-memory work is not incorrectly marked as saved.
- [ ] Confirm no infinite loading state or request loop occurs.
- [ ] Push the Sprint 20 branch only when asked: `sprint-20/reliable-sessions-save-safety-ci`.
- [ ] Observe the new GitHub Actions CI workflow on GitHub after push/PR.
- [ ] Verify the backend CI dependency install succeeds, especially the pinned Scrapling Git dependency.

## Priority 1 - Security And Auth Hardening

- [ ] Move refresh tokens out of `localStorage` and into secure `HttpOnly` cookies.
- [ ] Add CSRF protection when refresh-token cookies are introduced.
- [ ] Consider server-side refresh-token reuse detection for stricter rotation abuse handling.
- [ ] Complete the frontend token-to-cookie migration noted in the 10x roadmap.
- [ ] Add or expand a full cross-user authorization matrix.

## Priority 1 - Editor And Session Acceptance

- [ ] Complete Sprint 19 manual browser acceptance for beginner/professional editor flows.
- [ ] Complete Sprint 20 live browser acceptance for expired-session save/recovery flows.
- [ ] Verify that unrelated untracked local items are either intentionally ignored or cleaned up: `.thumbnail`, `screenshots/`, `uploads/`.

## Priority 2 - Layout Engine And Planning

- [ ] Complete richer graph-driven placement honoring `preferred_relative_position` and `requires_external_wall`.
- [ ] Implement true BSP footprint slicing by adjacency cluster instead of row clustering only.
- [ ] Decompose `generate_layout` into composable functions over a shared `BuildingModel`.
- [ ] Make `plot_width_m` and `orientation` affect row-banded fallback building types, not only tiled types.
- [ ] Add quality-scorer space-utilization metrics tied to parser adjacency satisfaction.
- [ ] Revisit whether BSP should apply to the front/open-plan row instead of only the back/private/service row.
- [ ] Add door-clearance checks and warnings.
- [ ] Improve refinement prompt handling and adjacency-aware refinement.

## Priority 2 - Canvas, Plan View, And Modeling Fidelity

- [ ] Add hover-triggered dimensions for non-selected rooms.
- [ ] Add rotation-aware dimension lines.
- [ ] Add a square-foot unit toggle for area badges.
- [ ] Build dimensioned plan-view rendering with door swings.
- [ ] Add persistent room-type color legend.
- [ ] Implement true internal wall topology with shared-wall deduplication.
- [ ] Punch real door/window openings into walls instead of marker boxes.
- [ ] Add room labels at centroids in floor-plan view.
- [ ] Expand 3D modeling fidelity: furniture, real wall/door/window geometry, materials/textures, roof, exterior facade, and better multi-floor building massing.

## Priority 2 - Export And Interop

- [ ] Implement SVG export.
- [ ] Implement DXF export.
- [ ] Implement glTF export.
- [ ] Plan CAD/BIM export work beyond current MVP exports.
- [ ] Revisit IFC/BIM support after the geometry model is more faithful.
- [ ] Improve PDF styling/report templates.
- [ ] Add cloud file storage for exports if/when needed.

## Priority 2 - Data Pipeline And Pattern Learning

- [ ] Add richer structured extraction with a `ScrapedProject` table.
- [ ] Add a real Spider crawler for project-level fields.
- [ ] Extract full room lists, per-room areas, and plan descriptors from public references.
- [ ] Add scheduled/background crawling and crawl queues.
- [ ] Build source-specific extraction adapters.
- [ ] Decide whether public scraper/source-management workflows should be exposed to normal users.
- [ ] Consider safe dependency caching or a dedicated backend test requirements file if CI install time is too high.

## Priority 3 - Collaboration, Workspace, And Product Surface

- [ ] Real-time collaboration.
- [ ] Pending email invitations and actual email sending.
- [ ] Comments.
- [ ] Notifications.
- [ ] Workspace billing.
- [ ] Public template marketplace.
- [ ] Mobile/tablet-specific UI.
- [ ] Advanced deployment automation.

## Priority 3 - AI, Optimization, And Advanced Validation

- [ ] Paid AI API integration.
- [ ] OpenAI, Claude, Gemini, or local model provider integration.
- [ ] Full AI model training or fine-tuning.
- [ ] LLM-based layout generation.
- [ ] Automatic self-learning from user edits.
- [ ] Complex spatial optimization algorithms.
- [ ] Advanced architectural validation.
- [ ] Structural validation.
- [ ] CAD/BIM reasoning.

## Stale Or Possibly Superseded TODOs To Audit

These appear as open or deferred in older sections, but later sprints likely completed or replaced them. Audit before implementing.

- [ ] Persistent per-object ActivityLog API remains listed as deferred from Sprint 6, but project activity history exists from Sprint 9B. Decide whether a true per-object API is still needed.
- [ ] Full version history panel is listed as deferred from Sprint 7, but Sprint 9A completed version history. Close the stale item if no extra panel work remains.
- [ ] Restore version UI is listed as deferred from Sprint 7, but Sprint 9A completed restore. Close the stale item if no extra restore work remains.
- [ ] Collaboration/version-control UI is listed as deferred from Sprint 7, but Sprint 9D completed basic workspaces. Clarify whether this now means real-time/version-control collaboration.
- [ ] AI training/layout-generation improvements were deferred from Sprint 10, but Sprint 11 delivered deterministic pattern-based improvements. Reframe this as the advanced AI backlog above.

## Non-Blocking Warnings To Revisit

- [ ] Frontend build warns that some chunks are larger than 500 kB after minification.
- [ ] Vite reports the CJS Node API deprecation warning during tests/build.
- [ ] Node warns that `frontend/postcss.config.js` is reparsed as an ES module because `package.json` does not declare `"type": "module"`.
- [ ] Backend tests emit a `python_multipart` pending deprecation warning through Starlette.
- [ ] React Router tests emit v7 future-flag warnings.

## Definition Of Done For Any TODO

- [ ] The scope is clearly tied to one TODO or tightly related group.
- [ ] Tests cover the regression or new behavior.
- [ ] Existing behavior remains backward-compatible unless the change intentionally migrates it.
- [ ] Frontend changes pass `npm test`, `npx tsc --noEmit`, and `npm run build`.
- [ ] Backend changes pass the relevant pytest subset and full backend suite when touching shared behavior.
- [ ] `CLAUDE.md` is updated when sprint status changes.
- [ ] This checklist is updated so completed work does not linger as noise.
- [ ] Commits are local until the user asks to push.
