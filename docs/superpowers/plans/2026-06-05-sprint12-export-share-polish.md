# Sprint 12 - Export, Share, and Polish

> **Date:** 2026-06-05  
> **Status:** In Progress  
> **Branch:** `sprint-12/export-share-polish`

## 1. Sprint Goal

Complete the ArchiAI MVP with practical project exports, revocable read-only share links, a focused interface-polish pass, full workflow verification, and deployment-ready setup documentation.

Sprint 12 improves delivery and usability around the existing project, layout, workspace, activity, and editor systems. It does not replace or broaden the existing generation and editing architecture.

## 2. MVP Scope

- Record authenticated image and PDF export actions for accessible projects.
- Export the current editor canvas as a PNG image.
- Export a basic project summary and layout preview as a PDF.
- Create and revoke token-based project share links.
- Provide a public read-only shared-project view containing only saved project and layout data.
- Log export and share actions through the existing activity system.
- Polish high-value dashboard, editor, export, share, loading, empty, and error states.
- Run a complete local MVP smoke flow and fix direct blockers.
- Update README, Docker, environment, and deployment-readiness documentation.

## 3. Excluded Scope

- CAD, BIM, DWG, IFC, or complex architectural export
- Cloud file storage or media CDN integration
- Paid APIs, billing, subscriptions, or quotas
- Real-time collaboration, comments, or notifications
- Editable public links or anonymous project mutation
- Password-protected links, link analytics, or expiring links
- Reworking deterministic generation, scraper, workspace, auth, or canvas architecture
- Advanced print-layout or architectural-document composition

## 4. Image Export Plan

The editor will capture the existing rendered canvas as a PNG data URL and trigger a browser download. After a successful client-side download, the frontend will call the authenticated backend image-export audit endpoint. The backend will record export metadata and activity without storing the image payload.

The export action must require project access, use a readable filename, and surface useful errors when canvas capture or audit logging fails.

## 5. PDF Export Plan

The frontend will create a lightweight MVP PDF containing project metadata and a current layout preview. It will use a small browser-compatible implementation and avoid server-side rendering or cloud storage.

After a successful download, the frontend will call the authenticated PDF-export audit endpoint. PDF export is a project handoff summary, not a CAD drawing or construction document.

## 6. Share Link Plan

Authenticated users with appropriate project access can create a token-based read-only share link and revoke active links. Share records are stored separately from project ownership and workspace membership.

The public token endpoint returns only the minimum saved project metadata and latest saved layout required by the shared view. It must not expose users, workspace membership, activity history, drafts, or internal version data.

## 7. Read-Only Shared View Plan

Add a public `/share/:token` route outside authenticated application routes. The page will render project information and the latest saved layout in a clearly read-only presentation.

Revoked or invalid tokens show a useful unavailable state. The shared page will not expose editor controls or permit any project mutation.

## 8. Activity Logging Plan

Use the existing `ActivityLog` system for:

- `project.exported`
- `project.shared`
- `project.share_revoked`

Activity metadata should include project ID and the relevant export type or share ID where practical. Existing activity views will receive readable labels for these actions.

## 9. UI Polish Checklist

- Keep export and sharing actions easy to find without crowding primary editor controls.
- Use existing design-system colors, spacing, buttons, dialogs, and status patterns.
- Improve loading, empty, success, and error states touched by Sprint 12.
- Verify toolbar and modal content does not overflow at common desktop and mobile widths.
- Keep shared views visibly read-only.
- Preserve all existing editor, history, activity, workspace, and autosave behavior.

## 10. End-to-End Testing Checklist

- Register or log in.
- Create and open a project.
- Generate or load a layout.
- Edit and manually save the layout.
- Download PNG and PDF exports.
- Confirm export activity entries.
- Create a share link and open it without authentication.
- Confirm shared layout is read-only and contains the latest saved layout.
- Revoke the share link and confirm it no longer opens.
- Verify private-project access checks with another user.
- Verify dashboard, workspace, editor, history, activity, scraper gating, and autosave remain functional.

## 11. README and Setup Update Plan

- Document local PostgreSQL, backend Uvicorn, and frontend startup commands.
- Document Docker Compose startup and migration commands.
- Document required and optional environment variables.
- Document export and share-link MVP behavior and limitations.
- Keep internal scraper/data-pipeline setup clearly separated from the normal user workflow.

## 12. Docker and Deployment Readiness Plan

- Confirm Docker services, ports, health checks, and environment configuration are consistent.
- Confirm Alembic upgrades apply from a fresh database.
- Confirm frontend production build and backend startup commands are documented.
- Document local-storage and public-share limitations.
- Avoid claiming production security, scalability, or persistence guarantees beyond the MVP.

## 13. Risks and Assumptions

- Browser canvas export may fail if future cross-origin assets taint the canvas.
- Client-generated PDFs are intentionally basic and browser-dependent.
- Share tokens provide possession-based read access; links must be treated as sensitive.
- Export records audit the action but do not store generated files.
- Public shared views rely on a saved design and do not expose unsaved drafts.
- Existing access-control helpers remain the source of truth for export and share creation.

## 14. Task Checklist

- [x] Task 0: Clean `CLAUDE.md` development-rule formatting
- [x] Task 1: Add Sprint 12 plan and checklist
- [ ] Task 2: Add backend export/share tests
- [ ] Task 3: Add backend export/share models and services
- [ ] Task 4: Add backend export/share API endpoints
- [ ] Task 5: Add frontend image export
- [ ] Task 6: Add frontend PDF export
- [ ] Task 7: Add shareable read-only project links
- [ ] Task 8: Integrate export/share activity labels
- [ ] Task 9: Polish MVP user interface
- [x] Task 10: Run and fix complete MVP smoke flow
- [ ] Task 11: Update README and deployment readiness
- [ ] Task 12: Run final checks and complete Sprint 12 documentation

## 15. Commit Plan

Each task receives a separate local commit after its relevant checks pass. Sprint 12 commits remain local until the branch owner explicitly pushes them.

1. `Fix CLAUDE development rules formatting`
2. `Add Sprint 12 export share polish plan`
3. `Add export and share backend tests`
4. `Add export and share backend models`
5. `Add export and share API endpoints`
6. `Add image export from editor`
7. `Add PDF project export`
8. `Add shareable read-only project links`
9. `Log export and share activity`
10. `Polish MVP user interface`
11. `Fix MVP smoke test issues`
12. `Update README and deployment setup`
13. `Complete Sprint 12 export share polish`

## 16. Task 10 Smoke Verification

Verified locally on 2026-06-05 against PostgreSQL migration `011`:

- Backend health and frontend development server respond on ports `8000` and `5173`.
- Registration, project creation, two-floor generation, manual save, separate auto-draft save, version listing, and version fetch pass.
- Image/PDF export audit records and project activity entries pass.
- Public share returns the latest saved layout, while draft-only changes remain private.
- Share revocation, private-project access checks, and project-delete share cleanup return the expected `403`/`404` responses.
- Workspace owner/editor shared-project access passes.
- Internal layout-pattern API remains available to authenticated internal tooling.
- Backend tests, frontend tests, and TypeScript checks pass.

Live canvas drag, browser downloads, and visual responsive inspection could not be clicked through because no in-app browser was attached. Existing editor, export-service, shared-view, and store tests cover these behaviors until a browser-assisted final manual pass is available.
