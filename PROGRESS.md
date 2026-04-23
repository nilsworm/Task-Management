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
- [x] API-Infrastruktur (DI, Exception-Handler, App-Struktur, CORS)
- [x] Pydantic-Schemas (Request/Response-DTOs)
- [x] Task-Router (/tasks)
- [x] Sprint-Router (/sprints)
- [x] Goal-Router (/goals) inkl. KeyResults
- [x] Dashboard-Router (/dashboard)
- [x] OpenAPI-Spec exportieren

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

### 2026-04-23 — Phase 4, Schritt 6+7: Dashboard-Router + OpenAPI-Export

- `dashboard_router.py`: `GET /dashboard` → total_tasks, task_counts (by status), total_goals, active_sprint (mit completion_percent)
- `openapi.json` exportiert: 15 Pfade (tasks, sprints, goals/key-results, dashboard, health)
- 4 neue Tests — **353 total passing**

### 2026-04-23 — Phase 4, Schritt 5: Goal-Router + KeyResults

- `KeyResult` domain entity (dataclass mit `progress_percent` property)
- `IGoalRepository` um 4 KeyResult-Methoden erweitert
- `PostgresGoalRepository`: `list_key_results`, `get_key_result`, `save_key_result`, `delete_key_result`
- `key_result_to_model`/`key_result_from_model` mapper
- `goal_use_cases.py`: CreateGoal, UpdateGoal, DeleteGoal, CreateKeyResult, UpdateKeyResult, DeleteKeyResult
- `goal_router.py`: CRUD /goals + CRUD /goals/{id}/key-results
- `KeyResultResponse.from_domain()`, `GoalUpdateRequest.to_use_case_input()`, KeyResult-Schema-Methoden
- 23 neue API-Tests — **349 total passing**

### 2026-04-23 — Phase 4, Schritt 4: Sprint-Router

- `src/api/routers/sprint_router.py`: POST/GET(list)/GET(active)/GET(detail)/PATCH/POST(start)/POST(complete)/POST(tasks/{id})/DELETE
- `GET /sprints/active` → `SprintResponse | None`
- `POST /sprints/{id}/tasks/{task_id}` → AddTaskToSprintUseCase
- 20 neue API-Tests — **326 total passing**

### 2026-04-23 — Phase 4, Schritt 3: Task-Router

- `src/api/routers/task_router.py`: POST/GET(list+filter)/GET(detail)/PATCH/POST(transition)/DELETE
- Filter: `?status=` via `list_by_status`, `?sprint_id=` via `list_by_sprint`
- `TaskFactory` singleton im Router (stateless, domain-only)
- 21 neue API-Tests gegen TestClient mit DI-Overrides — **306 total passing**

### 2026-04-23 — Phase 4, Schritt 2: Pydantic-Schemas

- `src/api/schemas/common.py`: `PriorityLiteral`, `StatusLiteral`
- `src/api/schemas/task_schemas.py`: `TaskCreateRequest.to_use_case_input()`, `TaskUpdateRequest.to_use_case_input()`, `TaskTransitionRequest.to_task_status()`, `TaskResponse.from_domain()` (isinstance-Dispatch für alle 4 Task-Typen)
- `src/api/schemas/sprint_schemas.py`: `SprintCreateRequest.to_date_range()`, `SprintResponse.from_domain()`
- `src/api/schemas/goal_schemas.py`: `GoalCreateRequest.to_domain()`, `GoalResponse.from_domain()`, `KeyResultCreate/Update/Response`
- 22 neue Mapping-Tests — **285 total passing**

### 2026-04-23 — Phase 4, Schritt 1: API-Infrastruktur

- `application/exceptions.py`: `EntityNotFoundError` (→ 404) + `InvalidOperationError` (→ 409)
- Use Cases: not-found → `EntityNotFoundError`, State-Machine-Fehler → `InvalidOperationError`
- `api/dependencies.py`: `get_session/task_repo/sprint_repo/goal_repo/event_bus` als `Depends()`-Provider
- `api/exception_handlers.py`: drei zentrale HTTP-Fehler-Handler (404 / 409 / 400)
- `src/main.py`: Handler registriert, CORS bestätigt (localhost:5173), `api/routers/` vorbereitet
- 13 neue Tests — **302 total passing**

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
