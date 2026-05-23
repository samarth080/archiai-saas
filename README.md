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
