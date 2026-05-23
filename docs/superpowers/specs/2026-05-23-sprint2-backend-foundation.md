# Sprint 2 — Backend Foundation: Design Spec

**Date:** 2026-05-23
**Status:** Approved
**Sprint Goal:** Core API infrastructure in place — Project CRUD, ActivityLog, and consistent structured error handling across all routes.

---

## Context

Builds on Sprint 1. The following already exist and must not be changed except where noted:
- `app/models/user.py` — User ORM model
- `app/schemas/auth.py` — auth schemas
- `app/services/auth_service.py` — `get_current_user(db, token)` returns `UserOut`
- `app/api/auth/router.py` — auth endpoints
- `app/utils/jwt.py`, `app/utils/hashing.py`
- `app/database/connection.py` — `Base`, `get_db()`
- `app/tests/conftest.py` — SQLite in-memory test fixtures

`GET /api/health` was implemented in Sprint 1 and requires no changes.

---

## Architecture

Three additions on top of the existing backend:

1. **Global error handler** — registered in `main.py`, intercepts all `HTTPException`s and reformats to `{ "error": str, "code": str, "status": int }`. Service logic raises plain `HTTPException` as before; the handler reshapes the response. Applies to all routes including existing auth endpoints.

2. **Project CRUD** — `Project` model, Alembic migration, schemas, service, and router at `/api/projects`. All endpoints require a valid Bearer token. Projects are scoped to the authenticated user.

3. **ActivityLog** — `ActivityLog` model, Alembic migration, and `log_activity()` utility called after each project write (create, update, delete). Internal only — no API endpoint.

New files follow the same structure as auth: one file per layer (`models/`, `schemas/`, `services/`, `api/`).

---

## Error Response Format

All `HTTPException`s are caught by the global handler and returned as:

```json
{
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "status": 404
}
```

**Status → code mapping:**

| Status | Code |
|---|---|
| 400 | `BAD_REQUEST` |
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `UNPROCESSABLE_ENTITY` |
| 500 | `INTERNAL_SERVER_ERROR` |

The handler is registered in `app/main.py`:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    500: "INTERNAL_SERVER_ERROR",
}

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": STATUS_CODES.get(exc.status_code, "ERROR"),
            "status": exc.status_code,
        },
    )
```

---

## Data Models

### Project (`app/models/project.py`)

| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key, server default |
| user_id | String | FK → users.id, indexed, not null |
| title | String(200) | Not null |
| description | Text | Nullable |
| created_at | DateTime (tz) | Server default UTC now |
| updated_at | DateTime (tz) | Updated on change |

### ActivityLog (`app/models/activity_log.py`)

| Column | Type | Notes |
|---|---|---|
| id | String (UUID) | Primary key, server default |
| user_id | String | FK → users.id, indexed, not null |
| action | String(100) | e.g. `"project.created"` |
| timestamp | DateTime (tz) | Server default UTC now |

Actions used in Sprint 2: `"project.created"`, `"project.updated"`, `"project.deleted"`

---

## Schemas (`app/schemas/project.py`)

```python
class ProjectCreate(BaseModel):
    title: str
    description: str | None = None

class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

class ProjectOut(BaseModel):
    id: str
    user_id: str
    title: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
```

---

## API Endpoints (`app/api/projects/router.py`)

All routes require `Authorization: Bearer <token>`. The token is verified via `get_current_user` from `auth_service`. Unauthenticated requests return `401 UNAUTHORIZED`.

| Method | Route | Auth | Description | Success |
|---|---|---|---|---|
| POST | `/api/projects` | Bearer | Create project | 201 + ProjectOut |
| GET | `/api/projects` | Bearer | List current user's projects | 200 + list[ProjectOut] |
| GET | `/api/projects/{id}` | Bearer | Get one project | 200 + ProjectOut |
| PUT | `/api/projects/{id}` | Bearer | Update title/description | 200 + ProjectOut |
| DELETE | `/api/projects/{id}` | Bearer | Delete project | 204 |

**Error cases:**
- No/invalid token → `401 { "error": "Not authenticated", "code": "UNAUTHORIZED", "status": 401 }`
- Project not found → `404 { "error": "Project not found", "code": "NOT_FOUND", "status": 404 }`
- Project belongs to another user → `403 { "error": "Access forbidden", "code": "FORBIDDEN", "status": 403 }`

---

## Service (`app/services/project_service.py`)

```python
async def create_project(db, user_id, data: ProjectCreate) -> ProjectOut
async def list_projects(db, user_id) -> list[ProjectOut]
async def get_project(db, user_id, project_id) -> ProjectOut  # raises 404/403
async def update_project(db, user_id, project_id, data: ProjectUpdate) -> ProjectOut
async def delete_project(db, user_id, project_id) -> None  # raises 404/403
```

Each write operation calls `log_activity(db, user_id, action)` after committing.

---

## Activity Logging (`app/utils/activity.py`)

```python
async def log_activity(db: AsyncSession, user_id: str, action: str) -> None:
    entry = ActivityLog(user_id=user_id, action=action)
    db.add(entry)
    await db.commit()
```

Called with fire-and-forget semantics inside service functions. Failures are caught and logged to stderr but do not raise (logging must never break the main request).

---

## Alembic Migrations

Two new migration files in `backend/alembic/versions/`:

- `002_create_projects.py` — creates `projects` table
- `003_create_activity_logs.py` — creates `activity_logs` table

Each depends on the previous revision.

---

## File Map

```
backend/app/
├── main.py                          MODIFY (add global error handler)
├── models/
│   ├── __init__.py                  MODIFY (add Project, ActivityLog imports)
│   ├── project.py                   CREATE
│   └── activity_log.py              CREATE
├── schemas/
│   └── project.py                   CREATE
├── services/
│   └── project_service.py           CREATE
├── utils/
│   └── activity.py                  CREATE
├── api/
│   └── projects/
│       ├── __init__.py              CREATE (empty)
│       └── router.py                CREATE
└── tests/
    ├── conftest.py                  NO CHANGE
    ├── test_auth.py                 MODIFY (update error assertions to new format)
    └── test_projects.py             CREATE

backend/alembic/versions/
├── 002_create_projects.py           CREATE
└── 003_create_activity_logs.py      CREATE
```

---

## Testing

### `test_auth.py` — Updates Required

The 4 tests that assert `response.json()["detail"]` must be updated to assert `response.json()["error"]` and `response.json()["code"]` instead:

- `test_register_duplicate_email` → assert `data["error"] == "Email already registered"`, `data["code"] == "CONFLICT"`
- `test_login_wrong_password` → assert `data["error"] == "Invalid email or password"`, `data["code"] == "UNAUTHORIZED"`
- `test_login_unknown_email` → assert `data["error"] == "Invalid email or password"`, `data["code"] == "UNAUTHORIZED"`
- `test_me_no_token` → assert `data["error"] == "Not authenticated"`, `data["code"] == "UNAUTHORIZED"`
- `test_me_invalid_token` → assert `data["error"] == "Not authenticated"`, `data["code"] == "UNAUTHORIZED"`

Note: `test_register_success`, `test_login_success`, `test_me_valid_token` have no error assertions and require no changes.

### `test_projects.py` — 8 New Tests

1. `test_create_project_success` — POST /api/projects → 201, returns id/title/user_id/created_at
2. `test_create_project_no_token` — POST /api/projects without auth → 401, code=UNAUTHORIZED
3. `test_list_projects_scoped_to_user` — register two users, each creates a project, GET /api/projects returns only the requester's
4. `test_get_project_success` — GET /api/projects/{id} → 200
5. `test_get_project_wrong_user` — GET /api/projects/{id} with different user's token → 403, code=FORBIDDEN
6. `test_update_project_success` — PUT /api/projects/{id} → 200, updated fields returned
7. `test_delete_project_success` — DELETE /api/projects/{id} → 204
8. `test_delete_project_wrong_user` — DELETE /api/projects/{id} with different user's token → 403

---

## Definition of Done (Sprint 2)

- [ ] Global error handler returns `{ error, code, status }` for all `HTTPException`s
- [ ] All existing auth tests updated and passing with new error format
- [ ] `POST /api/projects` creates a project and logs `"project.created"` to ActivityLog
- [ ] `GET /api/projects` returns only the authenticated user's projects
- [ ] `GET /api/projects/{id}` returns 403 for another user's project
- [ ] `PUT /api/projects/{id}` updates and logs `"project.updated"`
- [ ] `DELETE /api/projects/{id}` deletes and logs `"project.deleted"`, returns 204
- [ ] All 8 project tests passing
- [ ] All 8 auth tests still passing
- [ ] `docker-compose up` runs without errors with new migrations applied
