# Personal Task Management System

Local-only task manager (single user, no auth). FastAPI backend + React frontend + PostgreSQL.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [uv](https://docs.astral.sh/uv/) — Python dependency manager
- [pnpm](https://pnpm.io/) — Node package manager

## Setup

### 1. Environment

```bash
cp .env.example .env
```

### 2. Database

```bash
docker compose up -d
```

- Postgres: `localhost:5432`
- pgAdmin: `http://localhost:5050` (admin@local.dev / admin)

### 3. Backend

```bash
cd backend
uv sync
uv run uvicorn src.main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

- App: `http://localhost:5173`

## Run Tests

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
pnpm test
```
