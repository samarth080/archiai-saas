# Sprint 1 — Authentication and Project Setup: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full ArchiAI monorepo with a working FastAPI + PostgreSQL backend (JWT auth, 8 passing tests) and a React + TypeScript frontend (register, login, dashboard pages), all running from a single `docker-compose up`.

**Architecture:** Single monorepo with separate `backend/` and `frontend/` directories. FastAPI handles stateless JWT auth backed by PostgreSQL. React uses Zustand for auth state and React Router for guarded routes. Docker Compose orchestrates all three services (db, backend, frontend) with hot-reload volumes.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy (async), Alembic, asyncpg, python-jose, passlib/bcrypt, pytest, httpx, aiosqlite; React 18, TypeScript, Vite, Tailwind CSS, Zustand, Axios, React Hook Form, React Router v6

---

## File Map

```
archiai-saas/
├── docker-compose.yml                  CREATE
├── .env.example                        CREATE
├── README.md                           CREATE
├── backend/
│   ├── requirements.txt                CREATE
│   ├── pytest.ini                      CREATE
│   ├── Dockerfile                      CREATE
│   ├── alembic.ini                     CREATE
│   ├── alembic/
│   │   ├── env.py                      CREATE
│   │   └── versions/
│   │       └── 001_create_users.py     CREATE
│   └── app/
│       ├── __init__.py                 CREATE (empty)
│       ├── main.py                     CREATE
│       ├── config/
│       │   ├── __init__.py             CREATE (empty)
│       │   └── settings.py            CREATE
│       ├── database/
│       │   ├── __init__.py             CREATE (empty)
│       │   └── connection.py           CREATE
│       ├── models/
│       │   ├── __init__.py             CREATE (imports User)
│       │   └── user.py                 CREATE
│       ├── schemas/
│       │   ├── __init__.py             CREATE (empty)
│       │   └── auth.py                 CREATE
│       ├── utils/
│       │   ├── __init__.py             CREATE (empty)
│       │   ├── jwt.py                  CREATE
│       │   └── hashing.py              CREATE
│       ├── services/
│       │   ├── __init__.py             CREATE (empty)
│       │   └── auth_service.py         CREATE
│       ├── api/
│       │   ├── __init__.py             CREATE (empty)
│       │   └── auth/
│       │       ├── __init__.py         CREATE (empty)
│       │       └── router.py           CREATE
│       └── tests/
│           ├── __init__.py             CREATE (empty)
│           ├── conftest.py             CREATE
│           └── test_auth.py            CREATE
└── frontend/
    ├── package.json                    CREATE
    ├── tsconfig.json                   CREATE
    ├── tsconfig.node.json              CREATE
    ├── vite.config.ts                  CREATE
    ├── tailwind.config.ts              CREATE
    ├── postcss.config.js               CREATE
    ├── index.html                      CREATE
    ├── Dockerfile                      CREATE
    └── src/
        ├── index.css                   CREATE
        ├── main.tsx                    CREATE
        ├── App.tsx                     CREATE
        ├── types/
        │   └── auth.ts                 CREATE
        ├── store/
        │   └── authStore.ts            CREATE
        ├── services/
        │   └── auth.service.ts         CREATE
        ├── hooks/
        │   └── useAuth.ts              CREATE
        ├── components/
        │   ├── ui/
        │   │   ├── Button.tsx          CREATE
        │   │   └── Input.tsx           CREATE
        │   └── auth/
        │       ├── LoginForm.tsx       CREATE
        │       └── RegisterForm.tsx    CREATE
        └── pages/
            ├── Landing/index.tsx       CREATE
            ├── Login/index.tsx         CREATE
            ├── Register/index.tsx      CREATE
            └── Dashboard/index.tsx     CREATE
```

---

## Task 1: Root Infrastructure

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: ${DATABASE_URL}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
    command: sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: ${VITE_API_URL}
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
```

- [ ] **Step 2: Create `.env.example`**

```
POSTGRES_USER=archiai
POSTGRES_PASSWORD=archiai
POSTGRES_DB=archiai_db
DATABASE_URL=postgresql+asyncpg://archiai:archiai@db:5432/archiai_db
SECRET_KEY=change-this-in-production
VITE_API_URL=http://localhost:8000
```

- [ ] **Step 3: Copy to `.env`**

```bash
cp .env.example .env
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add docker-compose and env template"
```

---

## Task 2: Backend — Dependencies and Dockerfile

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/pytest.ini`
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
aiosqlite==0.20.0
alembic==1.13.1
pydantic[email]==2.7.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
pytest==8.2.0
pytest-asyncio==0.23.6
```

- [ ] **Step 2: Create `backend/pytest.ini`**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 3: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
```

- [ ] **Step 4: Commit**

```bash
git add backend/
git commit -m "feat: add backend requirements, pytest config, and Dockerfile"
```

---

## Task 3: Backend — Settings and Database Connection

**Files:**
- Create: `backend/app/__init__.py` (empty)
- Create: `backend/app/config/__init__.py` (empty)
- Create: `backend/app/config/settings.py`
- Create: `backend/app/database/__init__.py` (empty)
- Create: `backend/app/database/connection.py`
- Create: all other empty `__init__.py` files (models, schemas, utils, services, api, api/auth, tests)

- [ ] **Step 1: Create directory structure and all empty `__init__.py` files**

```bash
mkdir -p backend/app/config backend/app/database backend/app/models \
  backend/app/schemas backend/app/utils backend/app/services \
  backend/app/api/auth backend/app/tests \
  backend/alembic/versions

touch backend/app/__init__.py \
  backend/app/config/__init__.py \
  backend/app/database/__init__.py \
  backend/app/models/__init__.py \
  backend/app/schemas/__init__.py \
  backend/app/utils/__init__.py \
  backend/app/services/__init__.py \
  backend/app/api/__init__.py \
  backend/app/api/auth/__init__.py \
  backend/app/tests/__init__.py
```

- [ ] **Step 2: Create `backend/app/config/settings.py`**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str

    model_config = {"env_file": ".env"}


settings = Settings()
```

- [ ] **Step 3: Create `backend/app/database/connection.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/
git commit -m "feat: add backend app scaffold, settings, and async database connection"
```

---

## Task 4: Backend — User Model

**Files:**
- Create: `backend/app/models/user.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create `backend/app/models/user.py`**

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
```

- [ ] **Step 2: Write `backend/app/models/__init__.py`**

```python
from app.models.user import User  # noqa: F401 — registers User with Base.metadata

__all__ = ["User"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add User SQLAlchemy model"
```

---

## Task 5: Backend — Alembic Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/001_create_users.py`

- [ ] **Step 1: Create `backend/alembic.ini`**

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 2: Create `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config.settings import settings
from app.database.connection import Base
import app.models  # noqa: F401 — ensures all models register with Base.metadata

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Create `backend/alembic/versions/001_create_users.py`**

```python
"""create users table

Revision ID: 001
Revises:
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
```

- [ ] **Step 4: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: add Alembic config and initial users migration"
```

---

## Task 6: Backend — Auth Schemas and Utilities

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/utils/hashing.py`
- Create: `backend/app/utils/jwt.py`

- [ ] **Step 1: Create `backend/app/schemas/auth.py`**

```python
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
```

- [ ] **Step 2: Create `backend/app/utils/hashing.py`**

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

- [ ] **Step 3: Create `backend/app/utils/jwt.py`**

```python
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from app.config.settings import settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        return user_id
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/ backend/app/utils/
git commit -m "feat: add auth schemas, password hashing, and JWT utilities"
```

---

## Task 7: Backend — Test Fixtures

**Files:**
- Create: `backend/app/tests/conftest.py`

Tests use SQLite in-memory with `StaticPool` so all async sessions share the same in-memory database. FastAPI's `get_db` dependency is overridden per test via `app.dependency_overrides`.

- [ ] **Step 1: Create `backend/app/tests/conftest.py`**

```python
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.connection import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/tests/conftest.py
git commit -m "feat: add pytest fixtures with SQLite in-memory test database"
```

---

## Task 8: Backend — Write All 8 Failing Tests

**Files:**
- Create: `backend/app/tests/test_auth.py`

Write all tests before implementing the service or router. They will fail because `app.main` doesn't exist yet — that's the point.

- [ ] **Step 1: Create `backend/app/tests/test_auth.py`**

```python
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["name"] == "Test User"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"name": "Test User", "email": "dup@example.com", "password": "password123"}
    await client.post("/api/auth/register", json=payload)
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "securepass"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securepass"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={"name": "User", "email": "wrongpass@example.com", "password": "correctpass"},
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "wrongpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_unknown_email(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "somepass12"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_me_valid_token(client: AsyncClient):
    reg = await client.post(
        "/api/auth/register",
        json={"name": "Me User", "email": "me@example.com", "password": "mypassword"},
    )
    token = reg.json()["access_token"]
    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "me@example.com"


async def test_me_no_token(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


async def test_me_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/auth/me", headers={"Authorization": "Bearer thisisnotavalidtoken"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
```

- [ ] **Step 2: Verify tests fail (app.main does not exist yet)**

```bash
cd backend
pip install -r requirements.txt
SECRET_KEY=test DATABASE_URL=sqlite+aiosqlite:///:memory: pytest app/tests/test_auth.py -v
```

Expected: `ModuleNotFoundError` — `app.main` can't be imported. This confirms tests are wired up correctly, not accidentally passing.

- [ ] **Step 3: Commit**

```bash
git add backend/app/tests/test_auth.py
git commit -m "test: write all 8 auth endpoint tests (red)"
```

---

## Task 9: Backend — Auth Service

**Files:**
- Create: `backend/app/services/auth_service.py`

- [ ] **Step 1: Create `backend/app/services/auth_service.py`**

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.utils.hashing import hash_password, verify_password
from app.utils.jwt import create_access_token, decode_access_token


async def register_user(db: AsyncSession, data: RegisterRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        name=data.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


async def login_user(db: AsyncSession, data: LoginRequest) -> AuthResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    return AuthResponse(access_token=token, user=UserOut.model_validate(user))


async def get_current_user(db: AsyncSession, token: str) -> UserOut:
    try:
        user_id = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Not authenticated")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return UserOut.model_validate(user)
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/auth_service.py
git commit -m "feat: implement auth service (register, login, get_current_user)"
```

---

## Task 10: Backend — Auth Router and Main App

**Files:**
- Create: `backend/app/api/auth/router.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: Create `backend/app/api/auth/router.py`**

```python
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserOut
from app.services.auth_service import get_current_user, login_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    return await register_user(db, data)


@router.post("/login", response_model=AuthResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_user(db, data)


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def me(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: AsyncSession = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return await get_current_user(db, credentials.credentials)
```

- [ ] **Step 2: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth.router import router as auth_router

app = FastAPI(title="ArchiAI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/ backend/app/main.py
git commit -m "feat: add auth router and FastAPI app with CORS and health endpoint"
```

---

## Task 11: Backend — Run All 8 Tests (Green)

- [ ] **Step 1: Run tests and confirm all 8 pass**

```bash
cd backend
SECRET_KEY=testsecretkey DATABASE_URL=sqlite+aiosqlite:///:memory: pytest app/tests/test_auth.py -v
```

Expected output:
```
PASSED app/tests/test_auth.py::test_register_success
PASSED app/tests/test_auth.py::test_register_duplicate_email
PASSED app/tests/test_auth.py::test_login_success
PASSED app/tests/test_auth.py::test_login_wrong_password
PASSED app/tests/test_auth.py::test_login_unknown_email
PASSED app/tests/test_auth.py::test_me_valid_token
PASSED app/tests/test_auth.py::test_me_no_token
PASSED app/tests/test_auth.py::test_me_invalid_token

8 passed
```

If any test fails, debug before moving to the frontend.

- [ ] **Step 2: Commit green state**

```bash
git commit --allow-empty -m "test: all 8 auth tests passing (green)"
```

---

## Task 12: Frontend — Project Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/Dockerfile`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "archiai-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.7.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hook-form": "^7.51.5",
    "react-router-dom": "^6.23.1",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.4",
    "typescript": "^5.4.5",
    "vite": "^5.2.13"
  }
}
```

- [ ] **Step 2: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Create `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
  },
})
```

- [ ] **Step 5: Create `frontend/tailwind.config.ts`**

```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {},
  },
  plugins: [],
}

export default config
```

- [ ] **Step 6: Create `frontend/postcss.config.js`**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 7: Create `frontend/index.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ArchiAI</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 8: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
```

- [ ] **Step 9: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold frontend with Vite, React 18, TypeScript, Tailwind"
```

---

## Task 13: Frontend — Auth Types and Zustand Store

**Files:**
- Create: `frontend/src/types/auth.ts`
- Create: `frontend/src/store/authStore.ts`

- [ ] **Step 1: Create `frontend/src/types/auth.ts`**

```typescript
export interface UserOut {
  id: string
  name: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: UserOut
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}

export interface LoginRequest {
  email: string
  password: string
}
```

- [ ] **Step 2: Create `frontend/src/store/authStore.ts`**

```typescript
import { create } from 'zustand'

import { UserOut } from '../types/auth'

interface AuthState {
  user: UserOut | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: UserOut) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  login: (token, user) => {
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(user))
    set({ token, user, isAuthenticated: true })
  },
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null, isAuthenticated: false })
  },
}))

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return (payload.exp as number) * 1000 < Date.now()
  } catch {
    return true
  }
}

export function initAuthFromStorage(): void {
  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  if (!token || !userStr || isTokenExpired(token)) {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    return
  }
  try {
    const user = JSON.parse(userStr) as UserOut
    useAuthStore.setState({ token, user, isAuthenticated: true })
  } catch {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/ frontend/src/store/
git commit -m "feat: add auth types and Zustand store with localStorage persistence"
```

---

## Task 14: Frontend — Auth Service

**Files:**
- Create: `frontend/src/services/auth.service.ts`

- [ ] **Step 1: Create `frontend/src/services/auth.service.ts`**

```typescript
import axios from 'axios'

import { AuthResponse, LoginRequest, RegisterRequest, UserOut } from '../types/auth'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL as string,
})

export const authService = {
  register: (data: RegisterRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/register', data).then((r) => r.data),

  login: (data: LoginRequest): Promise<AuthResponse> =>
    api.post<AuthResponse>('/api/auth/login', data).then((r) => r.data),

  logout: (): Promise<void> => {
    const token = localStorage.getItem('token')
    return api
      .post('/api/auth/logout', {}, { headers: { Authorization: `Bearer ${token}` } })
      .then(() => undefined)
  },

  getMe: (): Promise<UserOut> => {
    const token = localStorage.getItem('token')
    return api
      .get<UserOut>('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.data)
  },
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/services/
git commit -m "feat: add frontend auth service (Axios wrapper for all auth endpoints)"
```

---

## Task 15: Frontend — useAuth Hook

**Files:**
- Create: `frontend/src/hooks/useAuth.ts`

- [ ] **Step 1: Create `frontend/src/hooks/useAuth.ts`**

```typescript
import { useNavigate } from 'react-router-dom'

import { authService } from '../services/auth.service'
import { useAuthStore } from '../store/authStore'
import { LoginRequest, RegisterRequest } from '../types/auth'

export function useAuth() {
  const { login, logout: clearStore, isAuthenticated, user } = useAuthStore()
  const navigate = useNavigate()

  async function register(data: RegisterRequest): Promise<void> {
    const response = await authService.register(data)
    login(response.access_token, response.user)
    navigate('/dashboard')
  }

  async function logIn(data: LoginRequest): Promise<void> {
    const response = await authService.login(data)
    login(response.access_token, response.user)
    navigate('/dashboard')
  }

  async function logOut(): Promise<void> {
    await authService.logout()
    clearStore()
    navigate('/')
  }

  return { register, logIn, logOut, isAuthenticated, user }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/hooks/
git commit -m "feat: add useAuth hook wrapping auth service and Zustand store"
```

---

## Task 16: Frontend — UI Components

**Files:**
- Create: `frontend/src/components/ui/Button.tsx`
- Create: `frontend/src/components/ui/Input.tsx`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p frontend/src/components/ui frontend/src/components/auth
```

- [ ] **Step 2: Create `frontend/src/components/ui/Button.tsx`**

```typescript
import { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary'
  loading?: boolean
  children: ReactNode
}

export function Button({
  variant = 'primary',
  loading = false,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  const base =
    'px-4 py-2 rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2'
  const variants = {
    primary:
      'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-indigo-500 disabled:opacity-50',
    secondary:
      'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400 disabled:opacity-50',
  }

  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={`${base} ${variants[variant]} ${className}`}
    >
      {loading ? (
        <span className="flex items-center gap-2">
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v8H4z"
            />
          </svg>
          {children}
        </span>
      ) : (
        children
      )}
    </button>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/ui/Input.tsx`**

```typescript
import { forwardRef, InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, ...props }, ref) => {
    const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')
    return (
      <div className="flex flex-col gap-1">
        <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          {...props}
          className={`border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
            error ? 'border-red-500' : 'border-gray-300'
          }`}
        />
        {error && <p className="text-xs text-red-600">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ui/
git commit -m "feat: add Button and Input UI components"
```

---

## Task 17: Frontend — Auth Forms

**Files:**
- Create: `frontend/src/components/auth/RegisterForm.tsx`
- Create: `frontend/src/components/auth/LoginForm.tsx`

- [ ] **Step 1: Create `frontend/src/components/auth/RegisterForm.tsx`**

```typescript
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { useAuth } from '../../hooks/useAuth'
import { RegisterRequest } from '../../types/auth'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function RegisterForm() {
  const { register: registerUser } = useAuth()
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterRequest>()

  async function onSubmit(data: RegisterRequest) {
    setLoading(true)
    setServerError('')
    try {
      await registerUser(data)
    } catch {
      setServerError('Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <Input
        label="Name"
        {...register('name', { required: 'Name is required' })}
        error={errors.name?.message}
      />
      <Input
        label="Email"
        type="email"
        {...register('email', { required: 'Email is required' })}
        error={errors.email?.message}
      />
      <Input
        label="Password"
        type="password"
        {...register('password', {
          required: 'Password is required',
          minLength: { value: 8, message: 'Password must be at least 8 characters' },
        })}
        error={errors.password?.message}
      />
      {serverError && <p className="text-sm text-red-600">{serverError}</p>}
      <Button type="submit" loading={loading}>
        Create Account
      </Button>
    </form>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/auth/LoginForm.tsx`**

```typescript
import { useState } from 'react'
import { useForm } from 'react-hook-form'

import { useAuth } from '../../hooks/useAuth'
import { LoginRequest } from '../../types/auth'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function LoginForm() {
  const { logIn } = useAuth()
  const [serverError, setServerError] = useState('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>()

  async function onSubmit(data: LoginRequest) {
    setLoading(true)
    setServerError('')
    try {
      await logIn(data)
    } catch {
      setServerError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <Input
        label="Email"
        type="email"
        {...register('email', { required: 'Email is required' })}
        error={errors.email?.message}
      />
      <Input
        label="Password"
        type="password"
        {...register('password', { required: 'Password is required' })}
        error={errors.password?.message}
      />
      {serverError && <p className="text-sm text-red-600">{serverError}</p>}
      <Button type="submit" loading={loading}>
        Sign In
      </Button>
    </form>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/auth/
git commit -m "feat: add LoginForm and RegisterForm with React Hook Form validation"
```

---

## Task 18: Frontend — Pages

**Files:**
- Create: `frontend/src/pages/Landing/index.tsx`
- Create: `frontend/src/pages/Login/index.tsx`
- Create: `frontend/src/pages/Register/index.tsx`
- Create: `frontend/src/pages/Dashboard/index.tsx`

- [ ] **Step 1: Create page directories**

```bash
mkdir -p frontend/src/pages/Landing frontend/src/pages/Login \
  frontend/src/pages/Register frontend/src/pages/Dashboard
```

- [ ] **Step 2: Create `frontend/src/pages/Landing/index.tsx`**

```typescript
import { Link } from 'react-router-dom'

import { Button } from '../../components/ui/Button'

export default function Landing() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-900 mb-2">ArchiAI</h1>
      <p className="text-gray-600 mb-8">
        AI-powered architectural design in your browser.
      </p>
      <div className="flex gap-4">
        <Link to="/register">
          <Button>Get Started</Button>
        </Link>
        <Link to="/login">
          <Button variant="secondary">Log In</Button>
        </Link>
      </div>
    </main>
  )
}
```

- [ ] **Step 3: Create `frontend/src/pages/Login/index.tsx`**

```typescript
import { Link } from 'react-router-dom'

import { LoginForm } from '../../components/auth/LoginForm'

export default function Login() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-gray-900">Sign In</h2>
        <LoginForm />
        <p className="mt-4 text-sm text-gray-600">
          Don&apos;t have an account?{' '}
          <Link to="/register" className="text-indigo-600 hover:underline">
            Register
          </Link>
        </p>
      </div>
    </main>
  )
}
```

- [ ] **Step 4: Create `frontend/src/pages/Register/index.tsx`**

```typescript
import { Link } from 'react-router-dom'

import { RegisterForm } from '../../components/auth/RegisterForm'

export default function Register() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-gray-900">Create Account</h2>
        <RegisterForm />
        <p className="mt-4 text-sm text-gray-600">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-600 hover:underline">
            Sign In
          </Link>
        </p>
      </div>
    </main>
  )
}
```

- [ ] **Step 5: Create `frontend/src/pages/Dashboard/index.tsx`**

```typescript
import { Button } from '../../components/ui/Button'
import { useAuth } from '../../hooks/useAuth'

export default function Dashboard() {
  const { user, logOut } = useAuth()

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white shadow px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">ArchiAI</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-600">Welcome, {user?.name}</span>
          <Button variant="secondary" onClick={logOut}>
            Logout
          </Button>
        </div>
      </header>
      <section className="p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Your Projects</h2>
        <p className="text-gray-500">
          No projects yet. Start a new design brief to get started.
        </p>
      </section>
    </main>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: add Landing, Login, Register, and Dashboard pages"
```

---

## Task 19: Frontend — App Routing and Entry Point

**Files:**
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`

- [ ] **Step 1: Create `frontend/src/App.tsx`**

```typescript
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'

import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import { useAuthStore } from './store/authStore'

function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />
}

function PublicOnlyRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Outlet />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<PublicOnlyRoute />}>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
```

- [ ] **Step 2: Create `frontend/src/main.tsx`**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'

import App from './App'
import './index.css'
import { initAuthFromStorage } from './store/authStore'

initAuthFromStorage()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/src/main.tsx
git commit -m "feat: add app routing with ProtectedRoute and PublicOnlyRoute guards"
```

---

## Task 20: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

````markdown
# ArchiAI

AI-powered architectural design platform.

## Local Setup

**Prerequisites:** Docker and Docker Compose

```bash
git clone https://github.com/samarth080/archiai-saas.git
cd archiai-saas
cp .env.example .env
docker-compose up
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Run Backend Tests

```bash
cd backend
pip install -r requirements.txt
SECRET_KEY=test DATABASE_URL=sqlite+aiosqlite:///:memory: pytest app/tests/ -v
```
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with local setup and test instructions"
```

---

## Task 21: Integration Test — docker-compose up

Final Definition of Done check from the spec.

- [ ] **Step 1: Build and start all services**

```bash
docker-compose up --build
```

Watch for these in the logs:
- `db` — `database system is ready to accept connections`
- `backend` — `INFO: Uvicorn running on http://0.0.0.0:8000`
- `frontend` — `Local: http://localhost:5173/`

- [ ] **Step 2: Check health endpoint**

```bash
curl http://localhost:8000/api/health
```

Expected: `{"status":"ok","version":"0.1.0"}`

- [ ] **Step 3: Smoke test register via curl**

```bash
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}' \
  | python3 -m json.tool
```

Expected: JSON with `access_token`, `token_type`, and `user`.

- [ ] **Step 4: Manual frontend flow**

1. Open http://localhost:5173 — Landing page visible.
2. Click "Get Started" → Register page. Fill form → Submit → lands on `/dashboard`.
3. Click Logout → redirected to `/`.
4. Navigate directly to http://localhost:5173/dashboard → redirected to `/login` (ProtectedRoute works).
5. Log in → `/dashboard` loads.
6. Refresh the page → still authenticated (localStorage restore works).

- [ ] **Step 5: Final commit and push**

```bash
git add -A
git commit -m "feat: complete Sprint 1 — auth backend + frontend + docker integration"
git push origin sprint-1/auth-setup
```

- [ ] **Step 6: Update Sprint 1 checklist in `CLAUDE.md`**

Change all Sprint 1 `- [ ]` items to `- [x]`, then:

```bash
git add CLAUDE.md
git commit -m "docs: mark Sprint 1 complete in CLAUDE.md"
git push origin sprint-1/auth-setup
```
