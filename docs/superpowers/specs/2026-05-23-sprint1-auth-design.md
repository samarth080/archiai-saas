# Sprint 1 — Authentication and Project Setup: Design Spec

**Date:** 2026-05-23
**Status:** Approved
**Sprint Goal:** Users can register, log in, and reach a personal dashboard. The full stack (FastAPI + PostgreSQL + React) runs locally with a single `docker-compose up`.

---

## Project Location

`~/Desktop/archiai-saas/`

This is a fresh monorepo connected to `github.com/samarth080/archiai-saas`. All code for this sprint goes here.

---

## Architecture

Single monorepo. Backend and frontend live side by side under one repo root. Docker Compose orchestrates all three services (Postgres, FastAPI, Vite) from a single command. Source directories are mounted as volumes for hot reload during development.

**Tech choices:**
- Backend: FastAPI + SQLAlchemy + Alembic + python-jose + passlib/bcrypt
- Frontend: React 18 + TypeScript + Vite + Tailwind CSS + React Router v6 + Zustand + Axios + React Hook Form
- Database: PostgreSQL 16 (Docker)
- Auth: Stateless JWT (HS256, 7-day expiry)

---

## Project Structure

```
~/Desktop/archiai-saas/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config/settings.py
│   │   ├── database/connection.py
│   │   ├── models/user.py
│   │   ├── schemas/auth.py
│   │   ├── api/auth/router.py
│   │   ├── services/auth_service.py
│   │   ├── utils/jwt.py
│   │   ├── utils/hashing.py
│   │   └── tests/test_auth.py
│   ├── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/Landing/index.tsx
│   │   ├── pages/Login/index.tsx
│   │   ├── pages/Register/index.tsx
│   │   ├── pages/Dashboard/index.tsx
│   │   ├── components/auth/LoginForm.tsx
│   │   ├── components/auth/RegisterForm.tsx
│   │   ├── components/ui/Button.tsx
│   │   ├── components/ui/Input.tsx
│   │   ├── store/authStore.ts
│   │   ├── services/auth.service.ts
│   │   └── hooks/useAuth.ts
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
├── docs/
│   ├── PROJECT_STRATEGY.md
│   └── superpowers/specs/2026-05-23-sprint1-auth-design.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Backend Design

### User Model (`app/models/user.py`)

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key, server default |
| email | String(255) | Unique, indexed, not null |
| hashed_password | String | Not null |
| name | String(100) | Not null |
| is_active | Boolean | Default true |
| created_at | DateTime | Server default UTC now |
| updated_at | DateTime | Updated on change |

### Auth Schemas (`app/schemas/auth.py`)

**Request — Register:**
```python
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str  # min length 8
```

**Request — Login:**
```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

**Response — Auth (both register and login return this):**
```python
class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class UserOut(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
```

### Auth Endpoints (`app/api/auth/router.py`)

| Method | Route | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | Public | Register new user, return JWT |
| POST | `/api/auth/login` | Public | Login, return JWT |
| POST | `/api/auth/logout` | Bearer | Client-side logout, return 200 |
| GET | `/api/auth/me` | Bearer | Return current user info |

**Error responses:**
- Duplicate email on register → `409 { "detail": "Email already registered" }`
- Wrong credentials on login → `401 { "detail": "Invalid email or password" }`
- Missing/invalid token → `401 { "detail": "Not authenticated" }`
- All other errors → `500 { "detail": "Internal server error" }`

### JWT (`app/utils/jwt.py`)

- Algorithm: HS256
- Expiry: 7 days (MVP)
- Payload: `{ "sub": user_id, "exp": expiry_timestamp }`
- Secret: `SECRET_KEY` from environment

### Password Hashing (`app/utils/hashing.py`)

- Library: `passlib[bcrypt]`
- Functions: `hash_password(plain: str) -> str` and `verify_password(plain: str, hashed: str) -> bool`

### Auth Service (`app/services/auth_service.py`)

- `register_user(db, data: RegisterRequest) -> AuthResponse`
- `login_user(db, data: LoginRequest) -> AuthResponse`
- `get_current_user(db, token: str) -> UserOut`

### Database (`app/database/connection.py`)

- SQLAlchemy async engine
- `get_db()` dependency yields a session per request
- `Base` declared here, imported by all models

### Settings (`app/config/settings.py`)

- `pydantic-settings` BaseSettings class
- Reads from environment: `DATABASE_URL`, `SECRET_KEY`

### Health Route

- `GET /api/health` → `{ "status": "ok", "version": "0.1.0" }`
- Registered in `main.py` alongside the auth router

---

## Frontend Design

### Routing (`App.tsx`)

```
/ → Landing (public)
/login → Login (public only — redirect to /dashboard if authenticated)
/register → Register (public only — redirect to /dashboard if authenticated)
/dashboard → Dashboard (protected — redirect to /login if not authenticated)
```

`ProtectedRoute` is a wrapper component: checks `isAuthenticated` from Zustand store, redirects to `/login` if false.

`PublicOnlyRoute` wrapper: redirects authenticated users away from `/login` and `/register` to `/dashboard`.

### Auth Store (`store/authStore.ts`)

Zustand store with:
```typescript
interface AuthState {
  user: UserOut | null
  token: string | null
  isAuthenticated: boolean
  login: (token: string, user: UserOut) => void
  logout: () => void
}
```

On `login()`: save token to `localStorage`, set state.
On `logout()`: clear `localStorage`, reset state.
On app load (`main.tsx`): read token from `localStorage`, decode it — if valid and not expired, restore auth state without an API call.

### Auth Service (`services/auth.service.ts`)

- `register(data): Promise<AuthResponse>` → `POST /api/auth/register`
- `login(data): Promise<AuthResponse>` → `POST /api/auth/login`
- `logout(): Promise<void>` → `POST /api/auth/logout`
- `getMe(): Promise<UserOut>` → `GET /api/auth/me`

Axios base URL read from `import.meta.env.VITE_API_URL`.

### Pages

**Landing (`/`):** Minimal — app name, one-line description, two CTAs: "Get Started" (→ /register) and "Log In" (→ /login). No styling complexity in Sprint 1.

**Register (`/register`):** RegisterForm component. Fields: Name, Email, Password. Inline validation errors. Submit calls `auth.service.register()`. On success → store token → navigate to `/dashboard`.

**Login (`/login`):** LoginForm component. Fields: Email, Password. Inline validation errors. Submit calls `auth.service.login()`. On success → store token → navigate to `/dashboard`.

**Dashboard (`/dashboard`):** Protected. Shows "Welcome, {name}" heading and a placeholder "Your Projects" section. Logout button calls `auth.service.logout()` then clears store and navigates to `/`.

### Reusable UI Components

- `Button.tsx` — primary/secondary variants, loading state (spinner), disabled state
- `Input.tsx` — label, error message prop, forwarded ref for React Hook Form

---

## Docker and Local Dev

### `docker-compose.yml` Services

| Service | Build | Port | Depends On |
|---|---|---|---|
| `db` | `postgres:16-alpine` | 5432 | — |
| `backend` | `backend/Dockerfile` | 8000 | `db` (healthy) |
| `frontend` | `frontend/Dockerfile` | 5173 | `backend` |

Backend and frontend source folders mounted as volumes for hot reload.

### Environment Variables (`.env.example`)

```
POSTGRES_USER=archiai
POSTGRES_PASSWORD=archiai
POSTGRES_DB=archiai_db
DATABASE_URL=postgresql+asyncpg://archiai:archiai@db:5432/archiai_db
SECRET_KEY=change-this-in-production
VITE_API_URL=http://localhost:8000
```

### To Run

```bash
git clone https://github.com/samarth080/archiai-saas.git ~/Desktop/archiai-saas
cd ~/Desktop/archiai-saas
cp .env.example .env
docker-compose up
```

- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Frontend: `http://localhost:5173`

---

## Testing

Pytest tests in `backend/app/tests/test_auth.py` using `httpx.AsyncClient` with a test database (SQLite in-memory or test Postgres via env override).

Tests cover:
- `POST /api/auth/register` — success case
- `POST /api/auth/register` — duplicate email returns 409
- `POST /api/auth/login` — success case returns token
- `POST /api/auth/login` — wrong password returns 401
- `POST /api/auth/login` — unknown email returns 401
- `GET /api/auth/me` — valid token returns user
- `GET /api/auth/me` — no token returns 401
- `GET /api/auth/me` — expired/invalid token returns 401

---

## Definition of Done (Sprint 1)

- [ ] `docker-compose up` starts all three services without errors
- [ ] `POST /api/auth/register` creates a user and returns a JWT
- [ ] `POST /api/auth/login` returns a JWT for valid credentials
- [ ] `GET /api/auth/me` returns user info for a valid token
- [ ] All 8 auth tests pass
- [ ] Register page creates an account and redirects to dashboard
- [ ] Login page authenticates and redirects to dashboard
- [ ] Dashboard is not accessible without a valid token
- [ ] Logout clears auth state and redirects to landing
- [ ] `.env.example` is complete and accurate
- [ ] README has local setup instructions
- [ ] All changes committed and pushed to `github.com/samarth080/archiai-saas`
