# ArchiAI

AI-powered architectural design platform. Users enter a natural language design brief and receive a 3D architectural layout they can view, edit, and refine in an interactive browser-based canvas.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router v6, Zustand |
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), Alembic, Pydantic v2 |
| Database | PostgreSQL 16 |
| Auth | JWT (HS256), bcrypt |
| Dev | Docker, Docker Compose |

---

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

---

## Turn On The Backend

### Option 1: Docker Compose

From the repo root:

```bash
cp .env.example .env
docker-compose up backend
```

The backend runs at `http://localhost:8000`.

### Option 2: Run Backend Locally

Start PostgreSQL first, then run the API from the `backend` folder.

PowerShell:

```powershell
cd backend
copy ..\.env.example .env
..\.venv311\Scripts\python.exe -m pip install -r requirements.txt
..\.venv311\Scripts\python.exe -m alembic upgrade head
..\.venv311\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

If you do not already have `.venv311`, create it from the repo root:

```powershell
py -3.11 -m venv .venv311
.\.venv311\Scripts\python.exe -m pip install --upgrade pip
```

Check that it is running:

```bash
curl http://localhost:8000/api/health
```

API docs are available at `http://localhost:8000/docs`.

> Note: when running the backend locally, `backend/.env` is used. If `DATABASE_URL` contains `@db:5432`, the app will fall back to `@localhost:5432` for local development when `db` is not resolvable.

---

## Populate Layout Pattern Data

Sprint 11 layout generation works without pattern records by using built-in fallback rules. To test the data-informed path locally, register a user and seed clearly labeled MVP pattern rows:

```powershell
cd backend
..\.venv311\Scripts\python.exe -m alembic upgrade head
..\.venv311\Scripts\python.exe -m scripts.seed_layout_patterns --user-email you@example.com
```

The seed command is idempotent and creates dev-only records with `source_url = "seed:mvp-patterns"`. You can also run vetted public-text sources explicitly from `http://localhost:5173/scraper`.

See [docs/PATTERN_DATA_WORKFLOW.md](docs/PATTERN_DATA_WORKFLOW.md) for the Sprint 10 to Sprint 11 workflow, API verification commands, and before/after test prompts.

---

## API Overview

### Auth
| Method | Route | Description |
|---|---|---|
| POST | `/api/auth/register` | Register new user, returns JWT |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/logout` | Client-side logout |
| GET | `/api/auth/me` | Get current user info |

### Projects
| Method | Route | Description |
|---|---|---|
| POST | `/api/projects` | Create a project |
| GET | `/api/projects` | List your projects |
| GET | `/api/projects/{id}` | Get a project |
| PUT | `/api/projects/{id}` | Update a project |
| DELETE | `/api/projects/{id}` | Delete a project |

All project endpoints require `Authorization: Bearer <token>`.

Error responses follow the format:
```json
{ "error": "Human-readable message", "code": "MACHINE_CODE", "status": 404 }
```

---

## Run Backend Tests

```bash
cd backend
pip install -r requirements.txt
SECRET_KEY=test DATABASE_URL=sqlite+aiosqlite:///:memory: pytest app/tests/ -v
```

---

## License

Copyright (c) 2026 Udai Batta & Samarth Chatli. All rights reserved.

This project is proprietary software. See [LICENSE](LICENSE) for full terms.
Unauthorized use, copying, or distribution is strictly prohibited and will have legal consequences.
