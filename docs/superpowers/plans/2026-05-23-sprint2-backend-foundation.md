# Sprint 2 — Backend Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add global HTTP error handler, Project CRUD with user scoping, and ActivityLog to the ArchiAI backend, with 16 total tests passing (8 auth + 8 project).

**Architecture:** Global `HTTPException` handler registered in `main.py` reshapes all errors to `{error, code, status}`. Project CRUD is layered (model → schema → service → router) mirroring the existing auth pattern. ActivityLog is written by the service layer after each write and never surfaces as an API endpoint.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Pydantic v2, pytest-asyncio, httpx, aiosqlite (tests)

---

## File Map

```
backend/app/
├── main.py                          MODIFY — add global error handler + projects router
├── models/
│   ├── __init__.py                  MODIFY — add Project, ActivityLog imports
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
    ├── test_auth.py                 MODIFY — 5 assertions changed from detail → error/code
    └── test_projects.py             CREATE

backend/alembic/versions/
├── 002_create_projects.py           CREATE
└── 003_create_activity_logs.py      CREATE
```

---

## Task 1: Global Error Handler + Update Auth Test Assertions

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/tests/test_auth.py`

- [ ] **Step 1: Run existing auth tests to confirm baseline**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/test_auth.py -v
```

Expected: 8 passed

- [ ] **Step 2: Add the global error handler to main.py**

Replace the entire contents of `backend/app/main.py` with:

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth.router import router as auth_router

app = FastAPI(title="ArchiAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


app.include_router(auth_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 3: Run auth tests — they should FAIL now (detail → error)**

```bash
python -m pytest app/tests/test_auth.py -v
```

Expected: 5 failures — the tests that assert `response.json()["detail"]`

- [ ] **Step 4: Update the 5 failing assertions in test_auth.py**

In `backend/app/tests/test_auth.py`, make these exact changes:

`test_register_duplicate_email` — replace:
```python
    assert response.json()["detail"] == "Email already registered"
```
with:
```python
    data = response.json()
    assert data["error"] == "Email already registered"
    assert data["code"] == "CONFLICT"
```

`test_login_wrong_password` — replace:
```python
    assert response.json()["detail"] == "Invalid email or password"
```
with:
```python
    data = response.json()
    assert data["error"] == "Invalid email or password"
    assert data["code"] == "UNAUTHORIZED"
```

`test_login_unknown_email` — replace:
```python
    assert response.json()["detail"] == "Invalid email or password"
```
with:
```python
    data = response.json()
    assert data["error"] == "Invalid email or password"
    assert data["code"] == "UNAUTHORIZED"
```

`test_me_no_token` — replace:
```python
    assert response.json()["detail"] == "Not authenticated"
```
with:
```python
    data = response.json()
    assert data["error"] == "Not authenticated"
    assert data["code"] == "UNAUTHORIZED"
```

`test_me_invalid_token` — replace:
```python
    assert response.json()["detail"] == "Not authenticated"
```
with:
```python
    data = response.json()
    assert data["error"] == "Not authenticated"
    assert data["code"] == "UNAUTHORIZED"
```

- [ ] **Step 5: Run auth tests — all 8 should pass**

```bash
python -m pytest app/tests/test_auth.py -v
```

Expected: 8 passed

- [ ] **Step 6: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/main.py backend/app/tests/test_auth.py
git commit -m "feat(sprint2): add global HTTPException handler, update auth test assertions"
```

---

## Task 2: Project ORM Model

**Files:**
- Create: `backend/app/models/project.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create backend/app/models/project.py**

```python
import uuid

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[object] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

- [ ] **Step 2: Update backend/app/models/__init__.py to import Project**

Replace the entire file with:

```python
from app.models.user import User  # noqa: F401 — registers User with Base.metadata
from app.models.project import Project  # noqa: F401 — registers Project with Base.metadata

__all__ = ["User", "Project"]
```

- [ ] **Step 3: Run existing tests to confirm no breakage**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/test_auth.py -v
```

Expected: 8 passed

- [ ] **Step 4: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/models/project.py backend/app/models/__init__.py
git commit -m "feat(sprint2): add Project ORM model"
```

---

## Task 3: ActivityLog Model + Utility

**Files:**
- Create: `backend/app/models/activity_log.py`
- Create: `backend/app/utils/activity.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create backend/app/models/activity_log.py**

```python
import uuid

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id"), nullable=False, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[object] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
```

- [ ] **Step 2: Create backend/app/utils/activity.py**

```python
import sys

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity_log import ActivityLog


async def log_activity(db: AsyncSession, user_id: str, action: str) -> None:
    try:
        entry = ActivityLog(user_id=user_id, action=action)
        db.add(entry)
        await db.commit()
    except Exception as exc:
        print(f"[activity log error] {exc}", file=sys.stderr)
```

- [ ] **Step 3: Update backend/app/models/__init__.py to import ActivityLog**

Replace the entire file with:

```python
from app.models.user import User  # noqa: F401 — registers User with Base.metadata
from app.models.project import Project  # noqa: F401 — registers Project with Base.metadata
from app.models.activity_log import ActivityLog  # noqa: F401 — registers ActivityLog with Base.metadata

__all__ = ["User", "Project", "ActivityLog"]
```

- [ ] **Step 4: Run tests to confirm no breakage**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/test_auth.py -v
```

Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/models/activity_log.py backend/app/utils/activity.py backend/app/models/__init__.py
git commit -m "feat(sprint2): add ActivityLog model and log_activity utility"
```

---

## Task 4: Alembic Migrations

**Files:**
- Create: `backend/alembic/versions/002_create_projects.py`
- Create: `backend/alembic/versions/003_create_activity_logs.py`

- [ ] **Step 1: Create backend/alembic/versions/002_create_projects.py**

```python
"""create projects table

Revision ID: 002
Revises: 001
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_user_id"), "projects", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_user_id"), table_name="projects")
    op.drop_table("projects")
```

- [ ] **Step 2: Create backend/alembic/versions/003_create_activity_logs.py**

```python
"""create activity_logs table

Revision ID: 003
Revises: 002
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_activity_logs_user_id"), "activity_logs", ["user_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_logs_user_id"), table_name="activity_logs")
    op.drop_table("activity_logs")
```

- [ ] **Step 3: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/alembic/versions/002_create_projects.py backend/alembic/versions/003_create_activity_logs.py
git commit -m "feat(sprint2): add Alembic migrations 002 (projects) and 003 (activity_logs)"
```

---

## Task 5: Project Schemas

**Files:**
- Create: `backend/app/schemas/project.py`

- [ ] **Step 1: Create backend/app/schemas/project.py**

```python
from datetime import datetime

from pydantic import BaseModel


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

- [ ] **Step 2: Confirm schemas import without error**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -c "from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/schemas/project.py
git commit -m "feat(sprint2): add Project schemas (ProjectCreate, ProjectUpdate, ProjectOut)"
```

---

## Task 6: Project Service

**Files:**
- Create: `backend/app/services/project_service.py`

- [ ] **Step 1: Write the failing test stubs in test_projects.py first (red)**

Create `backend/app/tests/test_projects.py`:

```python
from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, email: str) -> str:
    resp = await client.post(
        "/api/auth/register",
        json={"name": "User", "email": email, "password": "password123"},
    )
    return resp.json()["access_token"]


async def test_create_project_success(client: AsyncClient):
    token = await _register_and_token(client, "proj1@example.com")
    response = await client.post(
        "/api/projects",
        json={"title": "My First Project", "description": "A test project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My First Project"
    assert "id" in data
    assert "user_id" in data
    assert "created_at" in data


async def test_create_project_no_token(client: AsyncClient):
    response = await client.post(
        "/api/projects",
        json={"title": "No Auth Project"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "UNAUTHORIZED"


async def test_list_projects_scoped_to_user(client: AsyncClient):
    token_a = await _register_and_token(client, "user_a@example.com")
    token_b = await _register_and_token(client, "user_b@example.com")

    await client.post(
        "/api/projects",
        json={"title": "User A Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    await client.post(
        "/api/projects",
        json={"title": "User B Project"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = await client.get(
        "/api/projects", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["title"] == "User A Project"


async def test_get_project_success(client: AsyncClient):
    token = await _register_and_token(client, "get_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "Fetch Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Fetch Me"


async def test_get_project_wrong_user(client: AsyncClient):
    token_a = await _register_and_token(client, "owner@example.com")
    token_b = await _register_and_token(client, "intruder@example.com")

    created = await client.post(
        "/api/projects",
        json={"title": "Private Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    project_id = created.json()["id"]

    response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


async def test_update_project_success(client: AsyncClient):
    token = await _register_and_token(client, "update_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "Old Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.put(
        f"/api/projects/{project_id}",
        json={"title": "New Title", "description": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Updated"


async def test_delete_project_success(client: AsyncClient):
    token = await _register_and_token(client, "delete_proj@example.com")
    created = await client.post(
        "/api/projects",
        json={"title": "To Be Deleted"},
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = created.json()["id"]

    response = await client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    get_response = await client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


async def test_delete_project_wrong_user(client: AsyncClient):
    token_a = await _register_and_token(client, "del_owner@example.com")
    token_b = await _register_and_token(client, "del_intruder@example.com")

    created = await client.post(
        "/api/projects",
        json={"title": "Protected Project"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    project_id = created.json()["id"]

    response = await client.delete(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
```

- [ ] **Step 2: Run tests — expect failures (router doesn't exist yet)**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/test_projects.py -v
```

Expected: ImportError or 8 failures (404s from missing routes)

- [ ] **Step 3: Create backend/app/services/project_service.py**

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.utils.activity import log_activity


async def create_project(
    db: AsyncSession, user_id: str, data: ProjectCreate
) -> ProjectOut:
    project = Project(user_id=user_id, title=data.title, description=data.description)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    await log_activity(db, user_id, "project.created")
    return ProjectOut.model_validate(project)


async def list_projects(db: AsyncSession, user_id: str) -> list[ProjectOut]:
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    projects = result.scalars().all()
    return [ProjectOut.model_validate(p) for p in projects]


async def get_project(
    db: AsyncSession, user_id: str, project_id: str
) -> ProjectOut:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    return ProjectOut.model_validate(project)


async def update_project(
    db: AsyncSession, user_id: str, project_id: str, data: ProjectUpdate
) -> ProjectOut:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    if data.title is not None:
        project.title = data.title
    if data.description is not None:
        project.description = data.description
    await db.commit()
    await db.refresh(project)
    await log_activity(db, user_id, "project.updated")
    return ProjectOut.model_validate(project)


async def delete_project(
    db: AsyncSession, user_id: str, project_id: str
) -> None:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access forbidden")
    await db.delete(project)
    await db.commit()
    await log_activity(db, user_id, "project.deleted")
```

- [ ] **Step 4: Commit service (tests still failing — router next)**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/services/project_service.py backend/app/tests/test_projects.py
git commit -m "feat(sprint2): add ProjectService and test_projects (red — router pending)"
```

---

## Task 7: Project Router + Register in main.py

**Files:**
- Create: `backend/app/api/projects/__init__.py`
- Create: `backend/app/api/projects/router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create backend/app/api/projects/__init__.py (empty)**

Create the file with no content.

- [ ] **Step 2: Create backend/app/api/projects/router.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.auth_service import get_current_user
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)

router = APIRouter(prefix="/api/projects", tags=["projects"])
bearer = HTTPBearer(auto_error=False)


async def _current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> str:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = await get_current_user(db, credentials.credentials)
    return user.id


@router.post("", response_model=ProjectOut, status_code=201)
async def create(
    data: ProjectCreate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await create_project(db, user_id, data)


@router.get("", response_model=list[ProjectOut])
async def list_all(
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await list_projects(db, user_id)


@router.get("/{project_id}", response_model=ProjectOut)
async def get_one(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await get_project(db, user_id, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
async def update(
    project_id: str,
    data: ProjectUpdate,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await update_project(db, user_id, project_id, data)


@router.delete("/{project_id}", status_code=204)
async def delete(
    project_id: str,
    user_id: str = Depends(_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    await delete_project(db, user_id, project_id)
```

- [ ] **Step 3: Register the projects router in main.py**

Add the import and `include_router` call. The final `backend/app/main.py` should be:

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth.router import router as auth_router
from app.api.projects.router import router as projects_router

app = FastAPI(title="ArchiAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


app.include_router(auth_router)
app.include_router(projects_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 4: Run all tests — expect 16 passed**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/ -v
```

Expected: 16 passed (8 auth + 8 project)

- [ ] **Step 5: Commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add backend/app/api/projects/__init__.py backend/app/api/projects/router.py backend/app/main.py
git commit -m "feat(sprint2): add projects router, register in main — all 16 tests passing"
```

---

## Task 8: Update CLAUDE.md Sprint Progress

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark Sprint 2 complete and Sprint 1 complete in CLAUDE.md**

In the Sprint Progress section of `CLAUDE.md`, change:

```markdown
### Sprint 1 — Authentication and Project Setup 🔄 In Progress
```
to:
```markdown
### Sprint 1 — Authentication and Project Setup ✅ Complete
```

And change:
```markdown
### Sprint 2 — Backend Foundation ⏳ Not Started
```
to:
```markdown
### Sprint 2 — Backend Foundation ✅ Complete
- [x] Global error handler returns `{ error, code, status }` for all HTTPExceptions
- [x] All existing auth tests updated and passing with new error format
- [x] POST /api/projects creates a project and logs "project.created"
- [x] GET /api/projects returns only the authenticated user's projects
- [x] GET /api/projects/{id} returns 403 for another user's project
- [x] PUT /api/projects/{id} updates and logs "project.updated"
- [x] DELETE /api/projects/{id} deletes and logs "project.deleted", returns 204
- [x] All 8 project tests passing
- [x] All 8 auth tests still passing
```

- [ ] **Step 2: Run all tests one final time to confirm**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas/backend
python -m pytest app/tests/ -v
```

Expected: 16 passed

- [ ] **Step 3: Final commit**

```bash
cd /Users/samarthchatli/Desktop/archiai-saas
git add CLAUDE.md
git commit -m "docs: mark Sprint 1 complete, Sprint 2 complete in CLAUDE.md"
```

---

## Self-Review Checklist

- **Global error handler**: Task 1 — implemented in main.py, all auth tests updated ✅
- **All 5 auth test assertions updated** (duplicate_email, wrong_password, unknown_email, me_no_token, me_invalid_token): Task 1 ✅
- **Project model with all columns**: Task 2 — id, user_id, title, description, created_at, updated_at ✅
- **ActivityLog model**: Task 3 — id, user_id, action, timestamp ✅
- **log_activity swallows errors**: Task 3 — try/except prints to stderr ✅
- **Alembic migrations 002 + 003**: Task 4 ✅
- **Schemas (Create/Update/Out)**: Task 5 ✅
- **Service raises 404 for missing, 403 for wrong user**: Task 6 ✅
- **Each write op calls log_activity after commit**: Task 6 — create/update/delete ✅
- **All 5 router endpoints**: Task 7 — POST/GET list/GET one/PUT/DELETE ✅
- **Bearer auth dependency with 401 on missing token**: Task 7 — `_current_user_id` dep ✅
- **DELETE returns 204**: Task 7 — `status_code=204` on router ✅
- **8 project tests**: Task 6 — written in test_projects.py ✅
- **test_list_projects_scoped_to_user uses two separate users**: Task 6 ✅
- **CLAUDE.md updated**: Task 8 ✅
