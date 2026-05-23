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

Copyright (c) 2026 Samarth Chatli. All rights reserved.

This project is proprietary software. See [LICENSE](LICENSE) for full terms.
Unauthorized use, copying, or distribution is strictly prohibited and will have legal consequences.
