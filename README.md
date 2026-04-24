# Personal Task Management System

Local-only task manager for a single user — no auth, no cloud. Think Azure DevOps / Jira, but self-hosted on your machine.

**Features:** tasks with state machine · sprint kanban board (drag & drop) · OKR goals with key results · burndown / velocity / metrics dashboard · dark mode

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 async · Alembic · Pydantic v2 |
| Frontend | TypeScript · React 19 · Vite 8 · Tailwind v4 · shadcn/ui · TanStack Query · Recharts |
| Database | PostgreSQL 16 |
| Tests | pytest · Vitest · Playwright |
| Infra | Docker Compose · uv · pnpm |

---

## Prerequisites

| Tool | Install |
|---|---|
| Docker Desktop | https://www.docker.com/products/docker-desktop/ |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| pnpm | `npm install -g pnpm` |

---

## Option A — Full Docker stack

Builds and runs everything (Postgres, backend, frontend) in containers.

```bash
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5174 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

Migrations run automatically before the backend starts.

---

## Option B — Local development

Better for active development (hot-reload on both sides).

### 1. Environment

```bash
cp .env.example .env
```

### 2. Database (Docker)

```bash
docker compose up -d postgres pgadmin
```

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head          # run migrations
uv run uvicorn src.main:app --reload
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

- App: http://localhost:5173

---

## Seed data

Populate the database with realistic sample data (4 sprints, 31 tasks, 3 goals, 7 key results):

```bash
cd backend
uv run python -m scripts.seed          # idempotent upsert
uv run python -m scripts.seed --reset  # wipe all seed rows first, then insert
```

---

## Tests

### Backend — pytest

```bash
cd backend
uv run pytest                          # all 449 tests
uv run pytest --cov=src               # with coverage
```

### Frontend — Vitest (unit)

```bash
cd frontend
pnpm test                              # run once
pnpm test:watch                        # watch mode
```

### Frontend — Playwright (E2E)

Requires backend running and Playwright browser installed:

```bash
# Install browser once
cd frontend
pnpm exec playwright install chromium

# Run E2E tests
# (seeds the DB automatically if backend is reachable)
pnpm test:e2e
```

E2E tests cover: task CRUD · status transitions · sprint create/start · kanban drag & drop · goal/KR management · dashboard widgets.

---

## Project structure

```
/
├── backend/
│   ├── src/
│   │   ├── domain/          # entities, value objects, state machine
│   │   ├── application/     # use cases, services
│   │   ├── infrastructure/  # SQLAlchemy models, repositories
│   │   └── api/             # FastAPI routers, schemas, deps
│   ├── alembic/             # database migrations
│   ├── scripts/seed.py      # dev seed data
│   └── tests/
└── frontend/
    └── src/
        ├── api/             # generated types + TanStack Query hooks
        ├── features/        # tasks · sprints · goals · dashboard
        ├── components/      # shared UI components
        └── routes/          # React Router config
```

Architecture diagrams (Excalidraw): `/Excalidraw/`  
Design decisions: `/Excalidraw/design-decisions.md`

---

## Environment variables

Copy `.env.example` to `.env` and adjust as needed. All variables have working defaults.

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `taskmanager` | Database name |
| `POSTGRES_USER` | `taskmanager` | DB user |
| `POSTGRES_PASSWORD` | `taskmanager` | DB password |
| `POSTGRES_PORT` | `5432` | Host port for Postgres |
| `DATABASE_URL` | *(derived)* | Full asyncpg URL (local dev) |
| `BACKEND_PORT` | `8000` | Host port for backend |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:5174` | Allowed CORS origins |
| `FRONTEND_PORT` | `5174` | Host port for Dockerized frontend |
| `PGADMIN_EMAIL` | `admin@local.dev` | pgAdmin login |
| `PGADMIN_PASSWORD` | `admin` | pgAdmin password |
| `PGADMIN_PORT` | `5050` | Host port for pgAdmin |
