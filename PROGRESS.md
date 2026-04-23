# Personal Task Management System — Progress

## Tech-Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2
- **Frontend:** TypeScript, Vite, React, TanStack Query, Zustand, Tailwind, shadcn/ui, Recharts
- **DB:** PostgreSQL 16 (lokal via Docker Compose)
- **Tests:** pytest (Backend), Vitest + Playwright (Frontend)
- **Dependency Manager:** uv (Backend), pnpm (Frontend)

## Architektur-Referenz
- Klassendiagramm: `/Excalidraw/class-diagram.excalidraw`
- Architektur-Übersicht: `/Excalidraw/architecture-overview.excalidraw`
- Clean Architecture / DDD, keine Authentication (Single-User lokal)

## Phasenplan

### Phase 1 — Fundament ✅
- [x] Monorepo-Struktur (`/backend`, `/frontend`)
- [x] docker-compose.yml (Postgres 16 + pgAdmin, benannte Volumes)
- [x] Backend-Gerüst (FastAPI + SQLAlchemy async + Alembic async + pytest)
- [x] Frontend-Gerüst (Vite 8 + React 19 + Tailwind v4 + shadcn/ui konfiguriert)
- [x] .gitignore, .env.example, README

### Phase 2 — Domain-Layer (Backend)
- [ ] Value Objects: Priority, TaskStatus, Estimation, DateRange, Tag, BurndownPoint
- [ ] State Machine: ITaskState + alle States mit Übergängen
- [ ] Task-Hierarchie: abstract Task + DailyTask, SprintTask, LongTermGoal, Milestone
- [ ] TaskFactory (ITaskFactory)
- [ ] Domain Events + IEventBus (InMemoryEventBus)
- [ ] Unit Tests für Domain-Logik

### Phase 3 — Application & Infrastructure
- [ ] Repository-Interfaces: ITaskRepository, ISprintRepository, IGoalRepo
- [ ] SQLAlchemy-Models + erste Alembic-Migration
- [ ] Repository-Implementierungen (Postgres)
- [ ] Application Services / Use Cases
- [ ] Planning Strategies (Daily, Sprint, Monthly)
- [ ] Objective + KeyResult (OKR)
- [ ] Event-Handler für Dashboard-Updates

### Phase 4 — API-Layer
- [ ] FastAPI-Router: /tasks, /sprints, /goals, /dashboard
- [ ] Pydantic-Schemas (Request/Response)
- [ ] Dependency Injection für Repositories
- [ ] CORS für lokales Frontend
- [ ] OpenAPI-Spec prüfen

### Phase 5 — Frontend
- [ ] Types aus OpenAPI generieren (openapi-typescript)
- [ ] API-Client mit TanStack Query
- [ ] Layout + Routing (React Router)
- [ ] Task-Liste + Task-Detail
- [ ] Kanban-Board mit Drag & Drop
- [ ] Sprint-View
- [ ] Goals/OKR-View
- [ ] Dashboard mit Widgets (Burndown, Velocity, Completion Rate)

### Phase 6 — Polish
- [ ] E2E-Tests (Playwright)
- [ ] Seed-Daten für lokale Entwicklung
- [ ] Docker Compose: alles mit einem Befehl starten
- [ ] README finalisieren

## Session-Log

### 2026-04-22 — Phase 1 abgeschlossen
- Monorepo-Struktur angelegt (`/backend`, `/frontend`)
- `docker-compose.yml` mit Postgres 16 + pgAdmin (benannte Volumes)
- Backend: uv-Projekt, Python 3.12.13, FastAPI + SQLAlchemy async + Alembic async konfiguriert
- Backend-Test: `GET /health` → `{"status": "ok"}` ✅, `pytest` 1 passed ✅
- Frontend: Vite 8 + React 19 + TypeScript strict + Tailwind v4 + TanStack Query Provider
- `components.json` + `src/lib/utils.ts` für shadcn/ui vorbereitet
- `pnpm build` erfolgreich ✅
- `.gitignore`, `.env.example`, `README.md` angelegt
