# Sprint 9D: Team Collaboration / Workspaces

## 1. Sprint Goal

Users can create a workspace, add existing ArchiAI users as members, assign MVP roles, and collaborate through shared workspace projects with backend-enforced permissions and workspace activity history.

This sprint adds team structure and access control. It does not add real-time collaboration.

## 2. MVP Scope

- Workspace creation, listing, detail, update, and deletion.
- Workspace membership through a simple "add existing user by email" flow.
- Team member roles: `owner`, `admin`, `editor`, and `viewer`.
- Workspace member listing, role updates, and member removal.
- Optional `Project.workspace_id` association.
- Shared workspace project visibility and role-based access.
- Workspace-scoped activity logging for important team actions.
- Basic frontend workspace list, workspace detail, workspace project list, and member management UI.
- Backend tests for workspace CRUD, membership, permissions, workspace projects, and logging.
- Frontend typecheck and focused UI tests where practical.
- Existing personal projects continue to work unchanged when `workspace_id` is null.

## 3. Explicitly Excluded Scope

- WebSockets, live multi-user editing, cursor presence, or conflict resolution.
- Comments, chat, notifications, or email delivery.
- Pending invitations, invitation links, invitation expiry, or invitation acceptance flows.
- Workspace billing, subscriptions, quotas, or plan enforcement.
- Project-specific membership overrides (`ProjectMember`).
- Ownership transfer. The creator remains the immutable MVP workspace owner.
- Scraper/data-pipeline work, AI training, CAD/BIM export, or advanced enterprise controls.
- Unrelated canvas/editor changes.

## 4. Current Existing Functionality

### Backend

- JWT authentication and structured `{ error, code, status }` API errors.
- `User` model with unique email, active flag, and timestamps.
- Personal `Project` CRUD scoped directly by `Project.user_id`.
- Project duplication, latest design loading, manual save, named versions, draft auto-save, version history, and project activity.
- `ActivityLog` entries scoped by `user_id` and optional `project_id`.
- FastAPI routers for auth, projects, and designs.
- SQLAlchemy async services and Alembic migrations through revision `006`.
- Backend tests use SQLite in-memory tables through `Base.metadata.create_all`.

### Frontend

- Protected dashboard with personal project cards and project creation modal.
- Shared Axios client with bearer-token injection.
- Shared sidebar, project workspace page, editor, version history, activity drawer, and draft recovery flow.
- React Testing Library, Vitest, and happy-dom test setup.

## 5. Missing Functionality

- No `Workspace` model or persistence.
- No `TeamMember` model or role storage.
- No workspace API router, schemas, or collaboration service.
- No reusable read/write/admin permission helper for workspace-aware access.
- No optional project-to-workspace association.
- Project and design services assume direct personal ownership only.
- No `workspace_id` on activity logs and no workspace activity endpoint.
- No frontend workspace service, routes, pages, or member-management controls.

## 6. Proposed Database Models

### Workspace

| Field | Type | Notes |
|---|---|---|
| `id` | `String` UUID | Primary key, matching existing model convention |
| `name` | `String(200)` | Required |
| `description` | `Text` | Optional |
| `owner_id` | FK to `users.id` | Creator and immutable MVP owner |
| `created_at` | timezone timestamp | Server default |
| `updated_at` | timezone timestamp | Server default and update timestamp |

### TeamMember

| Field | Type | Notes |
|---|---|---|
| `id` | `String` UUID | Primary key |
| `workspace_id` | FK to `workspaces.id` | Indexed |
| `user_id` | FK to `users.id` | Indexed |
| `role` | `String(20)` | Validated as `owner`, `admin`, `editor`, or `viewer` |
| `created_at` | timezone timestamp | Membership creation time |

Constraints:

- Unique constraint on `(workspace_id, user_id)`.
- Workspace creation inserts an `owner` TeamMember row for the creator.
- The creator's owner membership cannot be removed or demoted during this MVP sprint.
- Adding a member with role `owner` is rejected because ownership transfer is deferred.

### Project Changes

Add nullable, indexed `workspace_id` FK to `workspaces.id`.

- `workspace_id = null`: existing personal project behavior.
- `workspace_id != null`: project is visible to workspace members and editable according to role.
- Keep `user_id` as the project creator/record owner for backward compatibility and audit attribution.

### ActivityLog Changes

Add nullable, indexed `workspace_id` column.

- Keep existing optional `project_id`.
- Workspace actions log `workspace_id`.
- Workspace project actions may log both `workspace_id` and `project_id`.

### Migration Plan

Create Alembic revision `007`:

1. Create `workspaces`.
2. Create `team_members` with unique membership constraint and indexes.
3. Add nullable indexed `projects.workspace_id`.
4. Add nullable indexed `activity_logs.workspace_id`.

Use nullable additions so existing PostgreSQL rows and personal-project behavior remain valid.

## 7. Proposed Backend Endpoints

Follow the existing plural project-router convention and global error format.

### Workspace CRUD

| Method | Endpoint | Permission | Purpose |
|---|---|---|---|
| `GET` | `/api/workspaces` | Authenticated | List workspaces where the current user is a member |
| `POST` | `/api/workspaces` | Authenticated | Create workspace and owner membership |
| `GET` | `/api/workspaces/{id}` | Workspace member | Get workspace detail |
| `PUT` | `/api/workspaces/{id}` | Owner/Admin | Update name or description |
| `DELETE` | `/api/workspaces/{id}` | Owner | Delete workspace, memberships, and detach projects |

### Members

| Method | Endpoint | Permission | Purpose |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/members` | Workspace member | List members and roles |
| `POST` | `/api/workspaces/{id}/members` | Owner/Admin | Add an existing user by email with selected/default role |
| `PUT` | `/api/workspaces/{id}/members/{member_id}/role` | Owner/Admin | Update non-owner member role |
| `DELETE` | `/api/workspaces/{id}/members/{member_id}` | Owner/Admin | Remove non-owner member |

Request for member add:

```json
{
  "email": "member@example.com",
  "role": "editor"
}
```

If the email is not registered, return `404` with `User not found`. Do not create a pending invite.

### Workspace Activity

| Method | Endpoint | Permission | Purpose |
|---|---|---|---|
| `GET` | `/api/workspaces/{id}/activity` | Workspace member | Return newest workspace-scoped team actions |

### Project Association

Extend the existing project payloads:

```json
{
  "title": "Shared Apartment",
  "description": "Workspace concept",
  "workspace_id": "workspace-uuid"
}
```

- `POST /api/projects` accepts optional `workspace_id`.
- `PUT /api/projects/{id}` accepts optional `workspace_id` changes where permitted.
- `ProjectOut` includes nullable `workspace_id`.
- `GET /api/projects` includes personal projects owned by the user and projects in the user's workspaces.

## 8. Proposed Frontend Pages and Components

### Routes

- `/workspaces`: workspace list and create flow.
- `/workspaces/:id`: workspace detail, shared projects, and member management.

### Service

Add `frontend/src/services/workspace.service.ts`:

- Workspace and team-member TypeScript interfaces.
- CRUD calls.
- Member list/add/update-role/remove calls.
- Workspace activity call if exposed in the UI.

Extend `project.service.ts` types so `workspace_id` is optional.

### Components

- `frontend/src/pages/Workspaces/index.tsx`
  - List workspaces.
  - Create workspace form or compact modal.
  - Loading, empty, and error states.
- `frontend/src/pages/Workspace/index.tsx`
  - Workspace header and description.
  - Shared project list.
  - Basic create-project action associated with the current workspace.
  - Member list.
- `frontend/src/components/workspaces/WorkspaceCard.tsx`
- `frontend/src/components/workspaces/CreateWorkspaceModal.tsx`
- `frontend/src/components/workspaces/MemberList.tsx`
- `frontend/src/components/workspaces/AddMemberForm.tsx`

Update `Sidebar` with a clear Workspaces navigation item while keeping Projects available.

Keep the UI work-focused and consistent with the current dashboard. No collaboration marketing surface is needed.

## 9. Access-Control Rules

### Workspace Roles

| Role | Workspace | Members | Workspace Projects |
|---|---|---|---|
| Owner | Read, update, delete | Add, change role, remove | Create, read, edit, delete |
| Admin | Read, update | Add, change non-owner role, remove non-owner | Create, read, edit, delete |
| Editor | Read | Read only | Create, read, edit |
| Viewer | Read | Read only | Read only |
| Non-member | No access | No access | No access |

### Personal Projects

- Existing direct owner behavior remains unchanged.
- A personal project has `workspace_id = null`.
- Only `Project.user_id` can read, edit, delete, duplicate, generate, refine, save, fetch drafts, list versions, and view activity.

### Workspace Projects

- Read permission: owner/admin/editor/viewer membership.
- Edit permission: owner/admin/editor membership.
- Delete permission: owner/admin membership.
- Workspace assignment/removal: owner/admin membership.
- Duplicate permission: any member who can read the source; the duplicate is personal by default unless a permitted target workspace is supplied later.
- `Design.user_id` remains the author of the design record, not the authorization boundary.

### Reusable Backend Helpers

Add collaboration access helpers in `workspace_service.py` or a small dedicated module:

- `get_workspace_member(...)`
- `require_workspace_role(...)`
- `get_accessible_project(...)`
- `require_project_read_access(...)`
- `require_project_edit_access(...)`
- `require_project_admin_access(...)`

Refactor project and design services to use these helpers only when Task 6 begins. Do not duplicate permission rules across routers.

## 10. Activity Log Actions

Reuse `ActivityLog` and extend `log_activity(..., workspace_id=None)`.

Required actions:

- `workspace.created`
- `workspace.updated`
- `workspace.deleted`
- `workspace.member_added`
- `workspace.member_role_changed`
- `workspace.member_removed`
- `project.added_to_workspace`
- `project.removed_from_workspace`

Workspace actions should be queryable through `/api/workspaces/{id}/activity`.

Do not add per-object workspace logging or new real-time event infrastructure in Sprint 9D.

## 11. Test Plan

### Backend Workspace CRUD

- Authenticated user can create a workspace.
- Creator becomes owner member.
- User lists only workspaces where they are a member.
- Member can fetch workspace detail.
- Owner/Admin can update workspace.
- Editor/Viewer/non-member cannot update workspace.
- Only owner can delete workspace.
- Workspace deletion detaches projects and removes memberships.

### Backend Member Management

- Owner/Admin can add an existing user by email.
- Missing user returns clear `404`.
- Duplicate membership returns `409`.
- Added member receives default `editor` or requested non-owner role.
- Members can list workspace members.
- Owner/Admin can change a non-owner member role.
- Owner/Admin can remove a non-owner member.
- Editor/Viewer cannot manage members.
- Owner cannot be demoted or removed.

### Backend Project Access

- Existing personal project tests continue to pass.
- Owner/Admin/Editor can create a workspace project.
- Viewer cannot create or edit a workspace project.
- Workspace members can list and open workspace projects.
- Non-members cannot read workspace projects.
- Owner/Admin can delete workspace projects.
- Editor/Viewer cannot delete workspace projects.
- Workspace editor can generate, load, manually save, refine, and auto-save draft layouts.
- Workspace viewer can load but cannot mutate layouts.
- Project workspace assignment/removal logs activity.

### Backend Workspace Activity

- Team actions create workspace-scoped entries.
- Workspace activity endpoint returns newest entries first.
- Non-members cannot read workspace activity.
- Existing project activity remains project scoped.

### Frontend

- Workspace service functions call expected endpoints and use the shared Axios client.
- Workspace list renders loading, empty, error, and populated states.
- Workspace create flow adds the new workspace.
- Workspace detail renders members and shared projects.
- Member add, role update, and remove controls call the service and update UI state.
- Viewer UI hides or disables mutating controls where practical.
- Existing frontend tests and `npx tsc --noEmit` remain green.

## 12. Task-by-Task Implementation Checklist

### Task 1: Sprint 9D Plan / Spec Document

- Create this implementation plan.
- Confirm MVP boundaries, access rules, model changes, endpoints, UI, tests, risks, and commit sequence.
- Commit: `Add Sprint 9D workspace collaboration plan`

### Task 2: Backend Workspace / Team Tests

- Add failing backend tests for workspace CRUD, member management, and access control.
- Keep production code unchanged except test scaffolding if required.
- Commit: `Add workspace backend tests`

### Task 3: Workspace and TeamMember Models / Migration

- Add `Workspace` and `TeamMember` models.
- Add Alembic revision `007`.
- Add nullable `Project.workspace_id` and `ActivityLog.workspace_id`.
- Export models through `app.models`.
- Run backend tests; Task 2 route tests may still fail until later tasks.
- Commit: `Add workspace and team member models`

### Task 4: Backend Workspace Services

- Add workspace CRUD service functions.
- Add member add/list/role/remove service functions.
- Add reusable workspace and project permission helpers.
- Keep services modular and testable.
- Commit: `Implement workspace service functions`

### Task 5: Workspace API Endpoints

- Add workspace schemas and router.
- Register workspace router.
- Expose CRUD, member management, and workspace activity endpoints.
- Run backend workspace tests and regression tests.
- Commit: `Add workspace API endpoints`

### Task 6: Project Workspace Association and Access Checks

- Extend project schemas with optional `workspace_id`.
- Apply reusable permission helpers to project services.
- Extend design services/routes so workspace roles authorize project-linked design operations.
- Preserve personal-project authorization behavior.
- Add and pass project/design workspace access tests.
- Commit: `Add project workspace access checks`

### Task 7: Frontend Workspace Service Functions

- Add workspace service types and API calls.
- Extend project types for nullable `workspace_id`.
- Run frontend typecheck and focused tests.
- Commit: `Add frontend workspace service functions`

### Task 8: Basic Workspace Dashboard UI

- Add workspace routes, list/create UI, detail shell, shared project list, and sidebar navigation.
- Reuse existing dashboard project-card patterns.
- Run frontend checks.
- Commit: `Add workspace dashboard UI`

### Task 9: Member Management UI

- Add member list, existing-user-by-email form, role controls, and remove action.
- Hide or disable mutating controls for editor/viewer roles.
- Run frontend checks and focused RTL tests where practical.
- Commit: `Add member management UI`

### Task 10: Activity Logs and Permissions Polish

- Log required workspace actions.
- Expose and verify workspace activity history.
- Audit permission consistency across project and design routes.
- Run backend tests and frontend checks if touched.
- Commit: `Polish workspace permissions and logs`

### Task 11: Final Checks and CLAUDE.md Update

- Run full backend `pytest`.
- Run frontend `npx tsc --noEmit`.
- Run frontend `npm test`.
- Update `CLAUDE.md` Sprint 9D checklist accurately.
- Mark Sprint 9D complete only if checks and manual validation pass.
- Commit: `Complete Sprint 9D workspace collaboration`

## 13. Risks and Assumptions

- Current authorization is embedded in project and design services as direct `user_id` checks. Task 6 must centralize project access helpers carefully so workspace access adds capability without weakening personal-project privacy.
- Current design queries filter by `Design.user_id`. Workspace project reads must query by project after access is granted, otherwise team members cannot load shared designs.
- SQLite test setup creates tables from SQLAlchemy metadata rather than running Alembic. Model imports in `app.models` must stay complete so new tables exist in tests.
- Workspace deletion should detach projects rather than delete them. This preserves user work and keeps deletion behavior predictable for the MVP.
- The strategy document mentions invitation links, owner transfer, and `ProjectMember`, but this sprint intentionally uses immediate add-existing-user membership and workspace-level inheritance only.
- `ActivityLog` currently stores a minimal action record. Add `workspace_id` only; richer metadata stays deferred.
- Existing users may have no workspaces. The dashboard and personal project flow must remain fully usable.

## 14. Commit Plan

Create local commits only on branch `sprint-9d/team-workspaces`. Do not push during the task sequence.

1. `Add Sprint 9D workspace collaboration plan`
2. `Add workspace backend tests`
3. `Add workspace and team member models`
4. `Implement workspace service functions`
5. `Add workspace API endpoints`
6. `Add project workspace access checks`
7. `Add frontend workspace service functions`
8. `Add workspace dashboard UI`
9. `Add member management UI`
10. `Polish workspace permissions and logs`
11. `Complete Sprint 9D workspace collaboration`

