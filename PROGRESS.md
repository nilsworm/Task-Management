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
- [x] Value Objects: Priority, TaskStatus, Estimation, DateRange, Tag, BurndownPoint
- [x] State Machine: ITaskState + alle States mit Übergängen
- [x] Task-Hierarchie: abstract Task + DailyTask, SprintTask, LongTermGoal, Milestone
- [x] TaskFactory (ITaskFactory)
- [x] Domain Events + IEventBus (InMemoryEventBus)
- [x] Unit Tests für Domain-Logik

### Phase 3 — Application & Infrastructure
- [x] Repository-Interfaces: ITaskRepository, ISprintRepository, IGoalRepo
- [x] SQLAlchemy-Models + erste Alembic-Migration
- [x] Repository-Implementierungen (Postgres)
- [x] Application Services / Use Cases
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

### 2026-04-23 — Phase 3: Schema-Nachbesserung (Migration 3)

- Index `ix_key_results_goal_id` auf `key_results.goal_id` ergänzt
- Model (`KeyResultModel`) mit `index=True` auf der Spalte aktualisiert
- `alembic check` meldet "No new upgrade operations detected" ✅

### 2026-04-23 — Phase 3: Schema-Fixes (Migration 2)

- FKs: tasks.sprint_id → sprints ON DELETE SET NULL; tasks.goal_id → goals ON DELETE SET NULL
- key_results Tabelle: id, goal_id (FK CASCADE), title, description, target_value, current_value, unit
- DROP sprint_task_ids (Redundanz); Sprint.task_ids jetzt via `tasks WHERE sprint_id = :id` geladen
- tags TEXT (JSON) → ARRAY(varchar[]) auf tasks + goals (Postgres-nativ)
- 5 Indizes auf tasks: status, sprint_id, goal_id, scheduled_date, task_type
- Models + Mapper + PostgresSprintRepository + Infra-Tests aktualisiert
- **289 Tests passing**

### 2026-04-22 — Phase 3, Step 4: Application Use Cases

- CreateTaskUseCase, UpdateTaskUseCase, TransitionTaskUseCase, DeleteTaskUseCase
- CreateSprintUseCase, StartSprintUseCase, CompleteSprintUseCase, AddTaskToSprintUseCase
- Fixed bug: estimation not forwarded to create_goal/create_milestone (unsupported by factory)
- EventSpy helper in tests/application/conftest.py for event-capture assertions
- 34 new unit tests (InMemory repos + EventBus, zero I/O) — **250 total passing**

### 2026-04-23 — Phase 2 abgeschlossen

- Value Objects: Priority, TaskStatus (Enums), Estimation, DateRange, Tag, BurndownPoint — 33 Tests ✅
- State Machine: ITaskState + 7 States (Backlog→Done/Cancelled), StateFactory — 58 Tests ✅
- Task-Hierarchie: abstract Task + DailyTask, SprintTask, LongTermGoal, Milestone — 35 Tests ✅
- TaskFactory: ITaskFactory + TaskFactory — 21 Tests ✅
- Domain Events: 6 Events + IEventBus + InMemoryEventBus — 28 Tests ✅
- Gesamt: 175 Domain-Tests + 1 Health-Test = **176 passing**
- Kein einziger Framework-Import im Domain-Layer

### 2026-04-22 — Phase 1 abgeschlossen
- Monorepo-Struktur angelegt (`/backend`, `/frontend`)
- `docker-compose.yml` mit Postgres 16 + pgAdmin (benannte Volumes)
- Backend: uv-Projekt, Python 3.12.13, FastAPI + SQLAlchemy async + Alembic async konfiguriert
- Backend-Test: `GET /health` → `{"status": "ok"}` ✅, `pytest` 1 passed ✅
- Frontend: Vite 8 + React 19 + TypeScript strict + Tailwind v4 + TanStack Query Provider
- `components.json` + `src/lib/utils.ts` für shadcn/ui vorbereitet
- `pnpm build` erfolgreich ✅
- `.gitignore`, `.env.example`, `README.md` angelegt
