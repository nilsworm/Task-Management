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
- Cost Management Architektur: Excalidraw (erstellt 2026-04-29, Branch `feature/cost-management`)
- Clean Architecture / DDD, keine Authentication (Single-User lokal)

## Phasenplan

### Phase 7 — Design-Refresh (feature/design-refresh)
- [x] Phase A — Backend: Sprint Goal-Feld
- [x] Phase B1 — Design-Tokens (Tailwind + shadcn)
- [x] Phase B2 — Layout & Sidebar
- [x] Phase B3 — Dashboard
- [x] Phase B4 — Tasks (Liste + Board-View-Switch)
- [x] Phase B5 — Sprints
- [x] Phase B6 — Goals
- [x] Phase B7 — Finale Durchsicht

### Phase 7 — Interaktions-Ergänzungen (Änderungen 1–5)
- [x] Phase A — Backend: completion_percent + RemoveTaskFromSprint + tags/due_date in UpdateTask
- [x] Phase B1 — TaskExpandedRow (inline edit in /tasks list), TaskTable + TasksPage vereinfacht
- [x] Phase B2 — Sprint-Detail: Kanban → SprintTaskList (inline expand), SprintTaskPicker, SprintInlineCreate, dnd-kit entfernt
- [x] Phase B3 — SprintCard + SprintDetailPage: Fortschrittsbalken + %
- [x] Phase B4 — TaskBoardView: Priority-Border + "→ Next"-Button, onEdit/onDelete entfernt

**Backlog (Daily Log — aus Scope-Entscheidung ausgenommen):**
- Daily Log mit Mood-Tracking und @Task-Mentions

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
- [ ] Planning Strategies (Daily, Sprint, Monthly) CANCELED ❌
- [x] Objective + KeyResult (OKR)
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
- [x] Schritt 1: API-Anbindung & Type-Generierung
- [x] Schritt 2: Layout & Routing
- [x] Schritt 3: Tasks-View
- [x] Schritt 4: Sprint-View (Kanban-Board)
- [x] Schritt 5: Goals-View
- [x] Schritt 6: Dashboard
- [x] Schritt 7: Polish & Smoke-Tests

### Phase 6 — Polish & Finalisierung
- [x] Schritt 1: Seed-Daten
- [x] Schritt 2: E2E-Tests (Playwright)
- [x] Schritt 3: Docker Compose vollständig
- [x] Schritt 4: Lücken & TODOs
- [x] Schritt 5: Dokumentation finalisieren
- [x] Schritt 6: Dev-Experience (Makefile / justfile, VS Code)
- [x] Schritt 7: Finale Architektur-Überprüfung

---

### Phase 11 — CSV Import (`feature/features`)

> Ziel: Importiere Bank-Transaktionen aus Consorsbank und Trade Republic CSV-Exporten in das Cost Management System.

#### Phase 11.1 — CSVParser Implementation ✅
**Liefergegenstand:** Utility-Modul zum Parsen von Consorsbank- und Trade Republic-CSV-Formaten

- [x] `InvalidCSVFormatError` und `InvalidTransactionDataError` Exception-Klassen
- [x] `CSVParser.parse_consorsbank(file_path)` — parst Consorsbank-Format
- [x] `CSVParser.parse_trade_republic(file_path)` — parst Trade Republic-Format
- [x] Handling von +/− Prefixen und Komma-Dezimaltrennzeichen
- [x] Standardisierte Dict-Struktur: `{date, amount, type, description}`
- [x] 6 Unit-Tests (Gültige CSVs, fehlende Spalten, ungültige Beträge) — alle grün
- [x] 565 Backend-Tests gesamt ✅

#### Phase 11.3 — Repository Extension for CSV Imports ✅
**Liefergegenstand:** CostRepository-Methode zum Persistieren geparster CSV-Zeilen

- [x] `ICostRepository.create_transaction_from_import(parsed_row, import_source)` Interface-Methode
- [x] `PostgresCostRepository.create_transaction_from_import()` Implementierung mit Typ-Konvertierung
- [x] `InMemoryCostRepository` Stub für Test-Kompatibilität ergänzt
- [x] 2 Integration-Tests (Consorsbank + Trade Republic Quellen)
- [x] 567 Backend-Tests gesamt ✅ (2 neue Tests, alle grün)

#### Phase 11.4 — ImportScheduler for Weekly Execution ✅
**Liefergegenstand:** Scheduler-Klasse, die /imports-Ordner scannt, Dateien verarbeitet und archiviert

- [x] `ImportScheduler` Service-Klasse in `src/application/services/import_scheduler.py`
- [x] `run_weekly_import()` async-Methode — scannt /imports, detectet Formate, parst, importiert, archiviert
- [x] Format-Detektion: consorsbank vs trade_republic via Filename-Pattern
- [x] Fehlerbehandlung: ungültige Dateien bleiben in /imports, einzelne Reihen-Fehler werden geloggt + ignoriert
- [x] Archive-Ordner (`/archived`) wird automatisch erstellt falls nicht vorhanden
- [x] Rückgabe: `{"status": "success", "imported": int, "files": [str]}`
- [x] 8 Unit-Tests (gültige Formate, mehrere Dateien, Fehlerbehandlung, leerer Ordner, unbekannte Formate, Reihen-Fehler)
- [x] 575 Backend-Tests gesamt ✅ (8 neue Tests, alle grün)

#### Phase 11.5 — CSV-Upload Endpoint (TODO)
**Liefergegenstand:** `POST /cost/import` akzeptiert hochgeladene CSV-Datei

- [ ] `ImportTransactionsUseCase` — orchestriert Parse + Batch-Save via `CSVParser`
- [ ] Endpoint `POST /cost/import` mit `file: UploadFile`
- [ ] Error-Handling: ungültige Formate, Duplikat-Warnung
- [ ] 409-Antwort wenn Transaktionen für Datum bereits existieren

#### Phase 11.6 — Frontend Import Dialog (TODO)
**Liefergegenstand:** UI zum Uploaden einer CSV-Datei mit Vorschau vor dem Importieren

- [ ] `CostImportDialog`: Datei-Upload, Trockentest-Vorschau (erste 5 Zeilen)
- [ ] Bestätigungsmodal mit importierten Transaktionsanzahl
- [ ] Toast-Feedback bei Erfolg/Fehler

---

### Phase 10 — Features (`feature/features`)

#### Phase 10.1 — Task-Textsuche
**Liefergegenstand:** Freitext-Suche über Titel im /tasks-View

- [ ] `ITaskRepository.list_by_search(query: str) -> list[Task]` + `PostgresTaskRepository` mit `ILIKE`
- [ ] `GET /tasks?search=` Query-Parameter im Router
- [ ] `TaskFilterBar`: debounced Texteingabe, steuert `search`-Filter
- [ ] `useTasks`-Hook: `search`-Parameter ergänzen
- [ ] Tests (UC/API/Vitest)

#### Phase 10.2 — Überfällige Tasks hervorheben
**Liefergegenstand:** Tasks mit `due_date < heute` und Status ≠ Done/Cancelled werden visuell markiert

- [ ] `GET /tasks?overdue=true` Backend-Filter (`due_date < today AND status NOT IN done/cancelled`)
- [ ] `ITaskRepository`: `overdue`-Filter in `list_all` oder neue `list_overdue`-Methode
- [ ] Frontend: roter visueller Indikator in `TaskTable` + `TaskBoardView`
- [ ] Optionaler Filter-Toggle in `TaskFilterBar`
- [ ] Tests

#### Phase 10.3 — Sprint-Abschluss-Zusammenfassung
**Liefergegenstand:** Modal vor "Complete" zeigt Velocity + erlaubt Backlog-Move für unfertige Tasks

- [ ] `CompleteSprintUseCase`: optionaler Parameter `move_incomplete_to_backlog: bool`
- [ ] `POST /sprints/{id}/complete` akzeptiert Body `{"move_incomplete_to_backlog": bool}`
- [ ] `SprintCompleteModal`: Zusammenfassung (done/offen, Velocity) + Checkbox für Backlog-Move
- [ ] `SprintDetailPage` / `SprintCard`: Button öffnet Modal statt direktem Aufruf
- [ ] Tests

#### Phase 10.4 — CSV Import für Finanz-Automation ✅
**Liefergegenstand:** Wöchentliches Parsing von Bank-CSVs (Consorsbank/Trade Republic), automatisches Scheduling, Archivierung, Import-Status-UI

- [x] Domain: `Transaction.import_source` field + migration
- [x] Infrastructure: `CSVParser` (Consorsbank + Trade Republic formats) — 6 tests
- [x] Application: `ImportScheduler` (weekly scan, parse, import, archive) — 8 tests
- [x] Repository: `create_transaction_from_import()` method — 2 integration tests
- [x] Config: `IMPORT_FOLDER` environment variable
- [x] Backend: APScheduler registration in FastAPI startup
- [x] API: `GET /cost/import-status` endpoint — 4 API tests
- [x] Frontend: `useImportStatus()` hook — 4 tests
- [x] Frontend: `ImportStatusCard` component — 4 tests
- [x] Frontend: CostManagementPage integration
- [x] Infrastructure: Docker `/imports` volume mount + .gitignore
- [x] Tests: Total 32 new tests (backend 12, frontend 8, API 4, integration 8) — all passing
- [x] Backend: 579 tests passing
- [x] Frontend: 95 tests passing
- [x] Commits: 17 commits total (one per subtask, Conventional Commits)

**Success Criteria:**
- ✅ Automatic weekly CSV imports (Monday 9am)
- ✅ Support for Consorsbank and Trade Republic formats
- ✅ Transaction persistence with import_source audit trail
- ✅ File archiving after successful import
- ✅ Frontend status display (last import date + count)
- ✅ Docker-ready (volume mount for /imports)
- ✅ No regressions in existing tests

---

### Phase 9 — Code-Optimierungen (`feature/code-optimizations`)

> Ziel: Bestehende N+1-Queries und sequentielle DB-Calls beseitigen, `UpdateTaskUseCase` um Feld-Leer-Funktion erweitern.

#### Phase 9.1 — N+1 in SprintRepository
**Liefergegenstand:** `list_all` lädt Task-IDs in einem Batch statt N Einzelabfragen

- [x] `PostgresSprintRepository._load_task_ids_bulk(sprint_ids)` — ein Query für alle Sprints
- [x] `list_all` nutzt Bulk-Methode statt Schleife mit `_load_task_ids`
- [x] Tests unverändert grün

#### Phase 9.2 — Batch-Queries in Dashboard Use Cases ✅
**Liefergegenstand:** Velocity und GoalProgress machen je einen DB-Call statt N

- [x] `ITaskRepository.list_by_sprint_ids(sprint_ids)` + Implementierung in `PostgresTaskRepository`
- [x] `GetVelocityUseCase`: Loop mit `list_by_sprint` → `list_by_sprint_ids`
- [x] `IGoalRepository.list_all_key_results()` + Implementierung in `PostgresGoalRepository`
- [x] `GetGoalProgressUseCase`: Loop mit `list_key_results` → `list_all_key_results` + Python-Gruppierung
- [x] Tests für neue Repo-Methoden + UC-Tests weiterhin grün

#### Phase 9.3 — UpdateTaskUseCase: Felder leeren ✅
**Liefergegenstand:** `due_date` lässt sich explizit auf `None` setzen

- [x] `UNSET`-Sentinel in `task_use_cases.py` — unterscheidet "nicht angegeben" von "explizit null"
- [x] `TaskUpdateRequest.to_use_case_input()` nutzt `model_fields_set` für `due_date`
- [x] 3 neue Tests — **506 passing**

---

### Phase 8 — Cost Management Refactoring (`feature/cost-refactoring`)

> Ziel: Code klein und effizient halten — Bulk-Save für atomare Monatsgenerierung, vollständiger Recurring-Lifecycle via is_active-Toggle, Monat-Navigation im Frontend.

#### Phase 8.1 — Backend: Bulk-Save + is_active-Toggle + Query-Optimierung
**Liefergegenstand:** Atomare Monatsgenerierung (ein Commit statt N), deaktivierbare Recurring-Einträge, schnellere Tag-Abfrage

- [x] `ICostRepository.save_transactions_bulk(transactions: list[Transaction]) -> None`
- [x] `PostgresCostRepository.save_transactions_bulk`: merge-Loop + ein Commit
- [x] `GenerateMonthlyUseCase`: N einzelne `save_transaction`-Calls → `save_transactions_bulk`
- [x] `list_all_tags` in `PostgresCostRepository`: 2 sequentielle Queries → ein SQL-UNION
- [x] `UpdateRecurringUseCase` + `UpdateRecurringInput(is_active: bool)`
- [x] `PATCH /cost/recurring/{id}`: `RecurringUpdateRequest` + Router-Endpoint
- [x] Tests: `UpdateRecurringUseCase` (UC) + `PATCH /cost/recurring/{id}` (API) — 503 BE passing
- [x] OpenAPI-Spec aktualisiert + TypeScript-Types neu generiert

#### Phase 8.2 — Frontend: Monat-Navigation + Code-Qualität
**Liefergegenstand:** Monat frei wählbar (Übersicht + Analyse), saubererer Code, konsistente Toast-Nutzung

- [x] `currentYearMonth()` → `src/lib/utils.ts` extrahieren (war in 2 Dateien dupliziert)
- [x] `CostManagementPage`: `generateMsg`-State → Sonner toast (konsistent mit restlichen Mutations)
- [x] `AnalyticsTab.tsx`: doppelten `useCostTags`-Import zusammengeführt
- [x] Monat-Navigation: Prev/Next-Buttons, State `{ year, month }` in `CostManagementPage`
- [x] `AnalyticsTab` bekommt `year`/`month` als Props statt eigenem `currentYearMonth()`
- [x] `RecurringList`: Pause/Play-Toggle-Button für `is_active` + `useToggleRecurring`-Hook
- [x] Vitest-Tests aktualisiert — 87 FE passing

---

### Phase 7 — Cost Management (`feature/cost-management`)

> Ziel: Ein vollständiges Kostenverwaltungs-Modul direkt im Task Manager. Nach jeder Phase ist etwas sichtbar und nutzbar.

#### Phase 7.1 — Domain + API Fundament ✅
**Liefergegenstand:** Funktionierendes Backend mit CRUD für Transaktionen und wiederkehrende Einträge (testbar via Swagger UI / curl)

- [x] Domain-Entities: `Transaction`, `RecurringTransaction` (dataclasses, pure Python)
- [x] Value Objects: `TransactionType` (INCOME/EXPENSE), `RecurrenceInterval` (WEEKLY/MONTHLY/YEARLY) — `amount: Decimal` direkt in Entity (YAGNI, kein Money-VO)
- [x] `ICostRepository` Interface (ABC, konsistent mit restlichem System)
- [x] Use Cases: `CreateTransactionUC`, `ListTransactionsUC`, `DeleteTransactionUC`, `CreateRecurringUC`, `ListRecurringUC`, `DeleteRecurringUC`, `ListCostTagsUC`
- [x] SQLAlchemy Models: `TransactionModel`, `RecurringTransactionModel` (Tabellen `cost_transactions`, `cost_recurring`)
- [x] `PostgresCostRepository` Implementierung
- [x] Alembic-Migration `a3f2e1d9c8b7` (manuell, FK `cost_transactions → cost_recurring`)
- [x] API-Router `/cost/transactions` (POST, GET, DELETE) + `/cost/recurring` (POST, GET, DELETE) + `/cost/tags` (GET)
- [x] Pydantic DTOs mit vollständiger Input-Validierung (amount `gt=0`, tags `max_length=50`, tag-Normalisierung)
- [x] `COST_CURRENCY` ENV-Variable in `config.py`
- [x] 49 neue Tests (5 Domain-VO, 13 Domain-Entity, 13 Use Case, 18 API) — **459 total passing**

**Security-Check:** Alle Inputs über Pydantic validiert, amount als `Decimal` mit `gt=0`, tags als `list[str]` mit `max_length` pro Tag, Vergangene-Monat-Schutz in DeleteTransactionUC (409).

---

#### Phase 7.2 — Frontend Grundansicht ✅
**Liefergegenstand:** „Cost Management"-Button in der Sidebar, Seite mit Transaktionsliste und Formularen zum Hinzufügen

- [x] Sidebar-Eintrag „Cost Management" (NavLink, Wallet-Icon)
- [x] `CostManagementPage` mit 3 Tabs: Übersicht | Regelmäßig | Analyse
- [x] `TransactionList`: Tabelle (Datum, Titel, Betrag, Typ, Tags) + Löschen
- [x] `TransactionCreateModal`: Titel, Betrag, Typ, Datum, Tags (Autocomplete), Beschreibung
- [x] `TransactionDeleteDialog` (inkl. Vergangenheits-Schutz-Hinweis)
- [x] `RecurringList`: Tabelle mit Interval-Badge + Aktiv/Inaktiv-Status
- [x] `RecurringCreateModal`: Titel, Betrag, Typ, Interval, Tag-of-month, Tags
- [x] `TransactionTypeBadge` + `formatAmount` (Hilfsfunktionen)
- [x] TanStack Query Hooks: `useTransactions`, `useCreateTransaction`, `useDeleteTransaction`, `useRecurring`, `useCreateRecurring`, `useDeleteRecurring`, `useCostTags`
- [x] OpenAPI-Types neu generiert (cost-Endpoints enthalten)
- [x] 9 neue Vitest-Tests (Badge, formatAmount, CostManagementPage Tab-Navigation) — **80 total passing**
- [x] `pnpm tsc --noEmit` → 0 Fehler

---

#### Phase 7.3 — Summary Cards + Tag-Filterung ✅
**Liefergegenstand:** Monatsübersicht (Einnahmen / Ausgaben / Saldo) als Cards oben, Filterung nach Tags

- [x] `GetCostSummaryUC`: Summe Einnahmen, Ausgaben, Saldo für laufenden Monat
- [x] `GET /cost/summary?year=YYYY&month=MM` API-Endpoint
- [x] `SummaryCards`-Komponente: Einnahmen (grün), Ausgaben (rot), Saldo (blau/rot je Vorzeichen)
- [x] `TagFilterBar` für Transaktionsliste (Multi-Select, Zurücksetzen-Button)
- [x] Backend-seitige Tag-Filterung bereits in `ListTransactionsUC` + Repo
- [x] Tests: 3 UC-Tests, 3 Router-Tests, 6 Vitest-Tests (SummaryCards)

---

#### Phase 7.4 — Diagramme & Analyse ✅
**Liefergegenstand:** Pie Chart (Ausgaben nach Tag) + Gegenüberstellung Einnahmen vs. Ausgaben pro Monat mit Tag-Filter

- [x] `GET /cost/analytics?year=YYYY&month=MM&tags=` API-Endpoint
- [x] `GetCostAnalyticsUseCase`: gruppierte Ausgaben nach Tag (sortiert nach Betrag) + Monatsvergleich letzte 6 Monate
- [x] `AnalyticsTab`-Komponente: PieChart (Donut, Ausgaben nach Tag) + BarChart (Einnahmen vs. Ausgaben je Monat)
- [x] Tag-Filter (TagFilterBar) auf Analyse-Tab wirkt auf beide Charts
- [x] Skeleton-Loading + Leerzustand-Handling (je Chart separat)
- [x] 8 neue Tests (4 UC, 4 API) — **584 Backend, 87 Frontend passing**

---

#### Phase 7.5 — Generierung + Polish ✅
**Liefergegenstand:** Automatische Übernahme wiederkehrender Einträge in den aktuellen Monat + vollständige UX

- [x] `GenerateMonthlyUC`: erstellt Transaktionen aus aktiven `RecurringTransaction`-Einträgen für einen Monat (idempotent via `recurring_source_id`)
- [x] `POST /cost/generate-monthly?year=YYYY&month=MM` — Button „Monat laden" in UI
- [x] Duplicate-Schutz: zweiter Aufruf überschreibt nicht, zeigt 409 wenn bereits generiert
- [x] E2E-Tests (Playwright): 6 Cost-Tests (serial mode), alle 33 E2E-Tests grün
- [x] Smoke-Tests: 2 neue Cost-Navigation-Tests, alle 10 Smoke-Tests grün
- [x] OpenAPI-Spec aktualisiert + TypeScript-Types neu generiert
- [x] Infrastruktur-Tests: `test_cost_repository.py` (13 Tests gegen echtes Postgres)
- [x] Vorhandene E2E-Bugs gefixt: dashboard strict-mode, goals delete-locator
- [ ] Rate-Limiting + Audit-Log: zurückgestellt bis Auth-System steht

---

## Session-Log

### 2026-05-14 — Phase 10.4: CSV Import für Finanz-Automation ✅

**Backend Implementation (Tasks 1-7):**
- Task 1: Transaction.import_source field + Alembic migration
- Task 2: CSVParser utility (Consorsbank + Trade Republic) — 6 tests
- Task 3: Repository.create_transaction_from_import() method — 2 tests
- Task 4: Config.IMPORT_FOLDER setting
- Task 5: ImportScheduler service (scan, parse, import, archive) — 8 tests
- Task 6: APScheduler registration in FastAPI (Monday 9am)
- Task 7: GET /cost/import-status endpoint — 4 tests
- Backend total: 12 new tests, 579 passing

**Frontend Implementation (Tasks 8-10):**
- Task 8: useImportStatus() TanStack Query hook — 4 tests
- Task 9: ImportStatusCard component (loading, empty, data states) — 4 tests
- Task 10: CostManagementPage integration
- Frontend total: 8 new tests, 95 passing

**Infrastructure (Tasks 11-12):**
- Task 11: Docker /imports volume mount + .gitignore
- Task 12: PROGRESS.md documentation

**Commits:** 17 total (subagent-driven development, TDD, frequent commits)
- Task 1: Domain extension + test coverage fix
- Task 2: CSVParser + temp file cleanup fix
- Task 3: Repository extension
- Task 4: Config
- Task 5: ImportScheduler
- Task 6: APScheduler registration
- Task 7: API endpoint
- Task 8: useImportStatus hook
- Task 9: ImportStatusCard component
- Task 10: CostManagementPage integration
- Task 11: Docker + .gitignore
- Task 12: PROGRESS.md

**Next Phase:** Phase 10.5 (optional) — POST /cost/import endpoint for manual CSV uploads, intelligent tag categorization (ML), duplicate detection

### 2026-05-14 — Phase 10.4: Consorsbank CSV Parser Fix ✅

**Issue:** CSVParser expected Consorsbank format with columns `Buchungstag, Wertstellung, Umsatzart, ...` with comma delimiter and YYYY-MM-DD dates. Real Consorsbank CSV export has different format: semicolon-delimited, metadata headers before transaction data, actual columns: `Buchung, Valuta, Sender / Empfänger, IBAN, BIC, Buchungstext, Verwendungszweck, Kategorie, Stichwörter, Umsatz geteilt, Betrag, Währung` with DD.MM.YYYY dates and German number format (1.234,56).

**Root Cause Analysis:** Code was written with assumptions about CSV format without verifying against actual Consorsbank exports. Spec provided expected format that didn't match real files.

**Fixes Applied:**
1. Updated `parse_consorsbank()` to skip metadata lines until "Kontoumsätze" section marker
2. Changed `csv.DictReader` delimiter from ',' to ';'
3. Changed date format parsing from "%Y-%m-%d" to "%d.%m.%Y"
4. Updated German number format handling: remove periods (thousands sep), replace commas with periods: `.replace(".", "").replace(",", ".")`
5. Fixed field name matching to handle trailing spaces from CSV
6. Updated test CSVs in `test_csv_parser.py` to include metadata headers and proper format

**Verification:** Parser successfully parses actual `imports/consorsbank.csv` with 87 real transactions. All 6 CSVParser tests passing.

**Commits:**
- `fix: update consorsbank csv test format to match actual file structure`

**Status:** Phase 10.4 now fully complete and verified with real data.

---

### 2026-05-14 — Task 9: ImportStatusCard Component for Frontend ✅

- **Component:** `src/features/cost/ImportStatusCard.tsx`
  - Displays last import date (formatted via `Intl.DateTimeFormat`)
  - Shows transaction count from most recent import
  - Shows loading skeleton (`Skeleton` component) while fetching
  - Shows empty state when no imports exist (dashed border, helpful text)
  - Uses design tokens: `border-border`, `bg-surface-2`, `bg-surface-3`, `text-secondary/tertiary`
- **Tests:** `src/features/cost/__tests__/ImportStatusCard.test.tsx` — 4 tests ✅
  - Renders import date and transaction count
  - Shows loading skeleton
  - Displays empty state for no imports
  - Handles single transaction label (grammar neutral: "X transactions")
- **Fixes:** TaskFilterBar test missing `search` field in default — added to support Phase 10.1
- **Status:** **95 Frontend tests passing** ✅, TypeScript 0 errors ✅, Build succeeds ✅
- **Commits:**
  - `feat: add ImportStatusCard component for displaying import status`
  - `fix: add missing search field to TaskFilterBar test default`
- **Next Step:** Phase 11.5 (CSV-Upload Endpoint POST /cost/import)

### 2026-05-14 — Task 8: useImportStatus Hook for Frontend ✅

- **Hook Implementation:** `useImportStatus()` added to `src/api/hooks/cost.ts`
  - Fetches from `GET /cost/import-status` endpoint
  - Returns `ImportStatus` type: `{ last_import_date: string | null, transaction_count: number }`
  - Configured with 60-second `refetchInterval` for polling latest status
- **Tests:** `src/api/__tests__/hooks.cost.test.tsx` — 4 tests
  - Fetch from API with correct endpoint
  - Handle empty state (no imports yet)
  - Error handling
  - Refetch interval configuration documented
- **Types:** Regenerated OpenAPI types, `import-status` endpoint now properly typed
- **Status:** **91 Frontend tests passing** ✅, TypeScript 0 errors ✅
- **Commit:** `feat: add useImportStatus hook for fetching import status from backend`
- **Next Step:** Phase 11.5 (CSV-Upload Endpoint POST /cost/import)

### 2026-05-14 — Task 7: Import Status Endpoint ✅

- **Endpoint:** `GET /cost/import-status`
  - Interface method `get_last_import_status()` → `ICostRepository`
  - Implementation in `PostgresCostRepository` — queries most recent imported transaction date + count
  - API endpoint returns `{last_import_date: ISO str | null, transaction_count: int}`
  - Filters only transactions with `import_source IS NOT NULL`
- **Tests:** 4 new API-level tests (empty, with imports, multiple imports, ignoring manual transactions)
- **Status:** **579 Backend-Tests passing** ✅ (4 new)
- **Commit:** `feat: add GET /cost/import-status endpoint`
- **Next Step:** Phase 11.6 (CSV-Upload Endpoint via POST /cost/import)

### 2026-05-14 — Phase 11.5: APScheduler Registration ✅

- **APScheduler Integration:** `backend/pyproject.toml` + `backend/src/main.py`
  - Added `apscheduler>=3.10.4` dependency
  - Registered AsyncIOScheduler in FastAPI startup event
  - Configures weekly job: Monday 9:00 AM (UTC)
  - Job invokes `ImportScheduler.run_weekly_import()` async method
  - Graceful shutdown of scheduler on app termination
  - Error logging if scheduler fails to start
- **Testing:** All 575 Backend-Tests passing ✅
- **Deprecation Note:** FastAPI `on_event` decorators are deprecated (should use lifespan context manager in future), but functional
- **Next Step:** Phase 11.6 (CSV-Upload Endpoint via POST /cost/import)

### 2026-05-14 — Phase 11.4: ImportScheduler for Weekly Execution ✅

- **ImportScheduler Service:** `src/application/services/import_scheduler.py` — Orchestrierung von CSV-Import
  - Scannt `/imports`-Ordner für `.csv`-Dateien
  - Detectet Format aus Filename-Pattern: `consorsbank` vs `trade_republic` / `traderepublic`
  - Parst via `CSVParser.parse_consorsbank()` oder `.parse_trade_republic()`
  - Erstellt Transactions via `cost_repo.create_transaction_from_import(parsed_row, import_source)`
  - Archiviert erfolgreiche Dateien in `/archived`-Ordner
  - Fehlerbehandlung: ungültig parsbare Dateien bleiben in `/imports`, einzelne Reihen-Fehler werden geloggt + ignoriert
- **Tests:** 8 Unit-Tests mit Temporary-Directories
  - Consorsbank-Format, Trade Republic-Format
  - Mehrere Dateien gleichzeitig
  - Fehlerbehandlung (ungültige Formate, unbekannte Formate)
  - Leerer Ordner
  - Archive-Ordner wird automatisch erstellt
  - Graceful Fehlerbehandlung bei einzelnen Reihen-Fehlern
- **Status:** 575 Backend-Tests gesamt, alle grün ✅
- **Commit:** feat: implement ImportScheduler for weekly CSV import and archiving
- **Nächster Schritt:** Phase 11.5 (CSV-Upload Endpoint)

### 2026-05-14 — Phase 11.3: Repository Extension for CSV Imports ✅

- **CostRepository Extension:** `ICostRepository.create_transaction_from_import()` + `PostgresCostRepository` Implementierung
  - Konvertiert geparste CSV-Zeilen (uppercase Typ) zu `Transaction`-Entities
  - Setzt `import_source` automatisch für Audit-Trail
  - Persistiert via existierende `save_transaction()`-Methode
- **Tests:** 2 neue Integration-Tests
  - `test_create_transaction_from_import_consorsbank`: Consorsbank-Quelle
  - `test_create_transaction_from_import_trade_republic`: Trade Republic-Quelle
- **Test-Infrastruktur:** `InMemoryCostRepository` um neue Methode erweitert (für Unit-Tests)
- **Status:** 567 Backend-Tests gesamt, alle grün ✅
- **Commit:** feat: add create_transaction_from_import method to CostRepository
- **Nächster Schritt:** Phase 11.2 (CSV-Upload Endpoint)

### 2026-05-14 — Phase 11.1: CSVParser Implementation ✅

- **CSVParser module:** `src/infrastructure/import_/csv_parser.py` mit 2 statischen Methoden
  - `parse_consorsbank(file_path)` — parst Consorsbank-Exporte (7-spaltig)
  - `parse_trade_republic(file_path)` — parst Trade Republic-Exporte (4-spaltig)
- **Exception-Handling:** `InvalidCSVFormatError` (fehlende Spalten), `InvalidTransactionDataError` (Parse-Fehler)
- **Features:**
  - +/− Prefix-Handling (Betrag mit Vorzeichen → absolut + type INCOME/EXPENSE)
  - Komma-Dezimaltrennzeichen-Support (EUR-Format)
  - `Decimal` für exakte Geldbeträge
  - Standardisierte Rückgabe: `[{"date": DATE, "amount": DECIMAL, "type": str, "description": str}]`
- **Tests:** 6 Unit-Tests, alle grün
  - Gültige CSVs (Consorsbank + Trade Republic)
  - Fehlende Spalten
  - Ungültige Beträge (InvalidOperation → InvalidTransactionDataError)
- **Commits:** 1 (feat: implement CSVParser for Consorsbank and Trade Republic formats)
- **Status:** 565 Backend-Tests gesamt, alle grün ✅

### 2026-04-24 — Phase 7, Interaktions-Ergänzungen B1–B4

- **B1 TaskExpandedRow:** Inline-Edit-Karte im /tasks-List-View — Save/Cancel/Delete, Status-Transition-Chips, Priority-Select (farbig), Estimation-Stepper, Tags, Due-Date, Description-Textarea; Priority-gefärbter linker Rand
- **B1 TaskTable:** Expandable rows via `expandedId`-State, Props auf `tasks + onDeleted?` reduziert
- **B1 TasksPage:** Modal-State + TaskEditModal/TaskDeleteDialog entfernt, TaskBoardView ohne onEdit/onDelete aufgerufen
- **B2 SprintTaskList:** Kompakte Listenspalten (Title, Status, Priority, Pts, ×), inline TaskExpandedRow bei Klick, × entfernt Task aus Sprint via `useRemoveTaskFromSprint`
- **B2 SprintTaskPicker:** Modal mit Search-Input, listet alle nicht-zugewiesenen Tasks, Single-Click assigned via `useAddTaskToSprint`
- **B2 SprintInlineCreate:** Inline-Titel-Eingabe in Sprint-Detail; erstellt Task mit task_type=sprint + sprint_id vorbelegt
- **B2 SprintDetailPage:** Kanban durch SprintTaskList ersetzt, "New Task" + "Assign existing"-Buttons, Fortschritt prominenter
- **B2 dnd-kit entfernt:** @dnd-kit/core + sortable + utilities aus package.json entfernt, KanbanBoard/Column/Card-Dateien gelöscht, KanbanBoard.test.tsx gelöscht
- **B3 SprintCard:** Fortschrittsbalken (bg-green, 100%-Breite = completion_percent%) + "X% · N tasks" Text
- **B3 SprintDetailPage:** Fortschritts-Panel (goal + Progress-Bar + done/total) oberhalb Controls
- **B4 TaskBoardView:** Priority-gefärbter linker Rand, "→ Next"-Button direkt auf Karte; TaskActions-Komponente entfernt
- **Fix:** `priority` State in TaskExpandedRow als `Priority`-Union-Typ (TaskResponse.priority ist `string` in generierten Types)
- **69 Tests grün** | Build sauber ✅

### **Phase 7 vollständig abgeschlossen ✅**

### 2026-04-24 — Phase 7, B3–B7: Dashboard / Tasks / Sprints / Goals / Polish

- **B3 Dashboard:** MetricsWidget (Pie + Legende + Tabelle), BurndownWidget, VelocityWidget, GoalProgressWidget — alle mit Design-Palette-Farben, Glow-Effekten, Mono-Typo, subtle Grid-Styling; `WidgetSkeleton`
- **B4 Tasks:** `TaskStatusBadge` neu (Design-Palette, kein Badge-Wrapper); `TaskFilterBar` kompakter; `TaskTable` als Grid-Layout (kein shadcn Table); `TaskBoardView` neu — 6 Kanban-Spalten, Task-Karten mit Priority-Dot; `TasksPage` mit List/Board-Toggle-Button
- **B5 Sprints:** `SprintStatusBadge` neu (Palette); `SprintCard` ohne shadcn Card, mit Goal-Feld; `SprintsPage` kompakter Header; `SprintDetailPage` mit Goal-Banner + neuem Back-Button; `KanbanColumn`/`KanbanTaskCard` auf Design-Palette
- **B6 Goals:** `GoalCard` ohne shadcn Card, Priority-Farbe für Progress-Bar + Badge; `GoalsPage` kompakter Header; `GoalDetailPage` neu; `KeyResultItem` mit lila Glow-Progressbar
- **B7 Polish:** `TaskActions` "Todo" → "To Do"; `SprintAssignTask` auf neues Button-/Select-Styling; Sweep: kein `text-2xl font-bold` mehr im Frontend
- **71 Tests grün** | Build sauber ✅

### 2026-04-24 — Phase 7, B2: Layout & Sidebar

- `AppLayout.tsx` komplett neu: `LogoMark` (Gradient-Box 24×24, "PD"), Brand "devflow"
- Sidebar-Nav: `border border-transparent` / `border-cyan/20 bg-cyan/10 text-cyan` für active, `hover:bg-surface-3` für inactive, Icon-Opacity
- Header: `GlobalStats` (Cyan/Green Dot + Count via `useMetrics`), Datum-Chip (mono), Divider, ThemeToggle — alles rechts
- Content-Padding: `p-3` (12px) statt `p-6`
- Test-Update: `useMetrics` gemockt, Assertions auf "devflow" + Stats
- **71 Tests grün** | Build sauber ✅

### 2026-04-24 — Phase 7, B1: Design-Tokens

- `index.html`: Titel → "devflow", Google Fonts (Inter + JetBrains Mono)
- `index.css`: Komplettes Token-System neu aufgebaut
  - `@theme`: `--font-sans/mono`, `--radius: 0.375rem`, shadcn semantic tokens (background/card/primary/muted/border/ring/destructive) für Light + Dark
  - Neue Design-Palette-Tokens: `--color-cyan/green/yellow/red/purple/orange`, Surface-Layer `surface-0…4`, `text-secondary/tertiary`, `border-strong`
  - `.dark`-Overrides: alle surface/text/border Tokens auf Design-Dark-Werte
  - Extra CSS-Variablen (`:root`/`.dark`): dim-Varianten, Shadow-Scale (4 Stufen), `--bg-radial`, `--overlay`
  - `@layer base`: box-sizing, body-Font, scrollbar (4px), antialiasing
- `App.css`: altes Vite-Starter-CSS geleert
- SprintCard-Test: `goal: null` im Mock ergänzt (neues Pflichtfeld)
- **69 Tests grün** | Build sauber ✅

### 2026-04-24 — Phase 7, Phase A: Backend Sprint Goal

- `Sprint`-Entity: `goal: str | None = None` ergänzt
- `SprintModel`: `goal TEXT NULL`-Spalte
- Mapper `sprint_to_model` / `sprint_from_model`: goal-Feld
- `SprintCreateRequest` + `SprintUpdateRequest`: `goal: str | None` (max 500 Zeichen)
- `SprintResponse`: `goal: str | None` + `from_domain()`
- `CreateSprintUseCase.execute`: `goal`-Parameter durchgeleitet
- `UpdateSprintUseCase.execute`: `name` und `goal` beide optional, unabhängig patchbar
- `sprint_router.py`: PATCH-no-op-Check auf `name is None and goal is None`
- Alembic-Migration `7013b7d457bf_add_sprint_goal_field.py`: `ADD COLUMN sprints.goal TEXT NULL`
- `alembic upgrade head` + `alembic check` ✅
- **457 Tests, alle grün** (8 neue)

### 2026-04-29 — Phase 7: Cost Management (7.1–7.3 + 7.5 abgeschlossen)

- Branch `feature/cost-management` → `feature/coolify-nginx-proxy` (nginx-Proxy für Coolify)
- Domain: `Transaction`, `RecurringTransaction`, `ICostRepository`, Value Objects
- Application: 8 Use Cases inkl. `GenerateMonthlyUC` (idempotent), `GetCostSummaryUC`
- Infrastructure: `PostgresCostRepository`, Alembic-Migration `a3f2e1d9c8b7`
- API: 8 Endpoints (`/cost/transactions`, `/cost/recurring`, `/cost/tags`, `/cost/summary`, `/cost/generate-monthly`)
- Frontend: `CostManagementPage` (3 Tabs), `SummaryCards`, `TagFilterBar`, `TransactionList/Modal/Delete`, `RecurringList/Modal`
- nginx-Proxy: `VITE_API_URL=/api`, `/api/` → `backend:8000` intern; Vite-Proxy für lokale Dev
- Seed-Script um Cost-Daten erweitert (6 Recurring, 12 Transaktionen)
- Tests: 528 Backend (davon 13 Infrastruktur-Integration), 18 Frontend-Unit, 33 E2E alle grün
- Phase 7.4 (Analyse-Charts) noch offen

### 2026-04-24 — Phase 6, Schritt 7: Finale Architektur-Überprüfung

- **Domain-Layer:** Null Framework-Imports bestätigt (reines Python/stdlib) ✅
- **Application-Layer:** Null Infrastructure/API-Imports — nur Domain-Interfaces und -Entities ✅
- **Repository-Symmetrie:** ITaskRepository, ISprintRepository, IGoalRepository — alle Interface-Methoden in Postgres-Implementierungen vorhanden, keine Extras ✅
- **Infrastructure-Layer:** Keine Business-Logik (nur `raise ValueError` in Mapper + bedingter Filter) ✅
- **ESLint-Fixes:**
  - `routes/index.tsx`: `NotFoundPage` in eigene Datei `features/shared/NotFoundPage.tsx` extrahiert
  - `TaskEditModal.tsx` + `GoalDetailPage/KeyResultEditModal.tsx`: `useEffect`-setState entfernt → lazy `useState`-Initializer + `key`-Prop in Eltern-Komponente
  - `badge.tsx` / `button.tsx` (shadcn/ui): `eslint-disable-next-line react-refresh/only-export-components` (standard shadcn-Pattern: Komponente + Variant-Funktion in einer Datei)
- `pnpm eslint src --max-warnings=0` → 0 Fehler ✅
- `pnpm tsc --noEmit` → 0 Fehler ✅

### **Phase 6 vollständig abgeschlossen ✅**

### 2026-04-24 — Phase 6, Schritt 6: Dev-Experience

- `Makefile`: 17 Targets — `install`, `up/down`, `migrate`, `migration n=…`, `backend`, `frontend`, `seed/seed-reset`, `test/test-be/test-fe/test-e2e`, `build/docker/logs`, `clean`; `make help` gibt strukturierte Übersicht aus
- `.vscode/settings.json`: Python-Interpreter auf `backend/.venv`, pytest-Discovery, Prettier für TS/TSX, Tailwind-Regex für cn(), Vitest rootConfig, Datei-Exclusions
- `.vscode/extensions.json`: Empfehlungen — Pylance, Prettier, ESLint, Tailwind CSS, Vitest Explorer, Playwright, Docker, GitLens
- `.vscode/launch.json`: 3 Debug-Configs — FastAPI starten, pytest (alle), pytest (aktuelle Datei)

### 2026-04-24 — Phase 6, Schritt 5: Dokumentation finalisieren

- `README.md` komplett überarbeitet: Tech-Stack-Tabelle, Option A (Docker full-stack), Option B (lokale Entwicklung), Seed-Anleitung, Test-Commands (pytest/Vitest/Playwright), Projektstruktur-Übersicht, Env-Variablen-Tabelle

### 2026-04-24 — Phase 6, Schritt 4: Lücken & TODOs

- `src/api/hooks/sprints.ts`: `useAddTaskToSprint(sprintId)` Hook ergänzt — `POST /sprints/{id}/tasks/{task_id}`
- `src/features/tasks/TaskFilterBar.tsx`: Status/Priority/Type-Labels kapitalisiert (STATUS_LABELS Map statt `replace("_", " ")`) — konsistent mit TaskStatusBadge
- `src/routes/index.tsx`: Catch-all Route `"*"` → `NotFoundPage` (inline, 404 + Link zu Dashboard)
- `src/features/tasks/TaskCreateModal.tsx`: Sprint-Typ-Feld: roher UUID-Input → `<Select>` mit `useSprints()` (Name + Status)
- `src/features/sprints/SprintAssignTask.tsx`: Neue Komponente — lädt unassigned SprintTasks via `useTasks()`, zeigt Select + Assign-Button
- `src/features/sprints/SprintDetailPage.tsx`: `<SprintAssignTask>` eingebunden (nur für planned/active Sprints, `task_ids` als assignedTaskIds übergeben)
- 69 Tests weiterhin grün, tsc sauber ✅

### 2026-04-24 — Phase 6, Schritt 3: Docker Compose vollständig

- `backend/src/config.py`: `cors_origins: str` Feld (kommagetrennt, default: localhost:5173,5174)
- `backend/src/main.py`: CORS nutzt `settings.cors_origins` statt Hardcode
- `backend/Dockerfile`: python:3.12-slim + uv, CMD: `alembic upgrade head && uvicorn`
- `backend/.dockerignore`: .venv, __pycache__, tests, .env ausgeschlossen
- `frontend/Dockerfile`: 2-Stage — node:22-alpine build (VITE_API_URL als ARG) → nginx:alpine serve
- `frontend/nginx.conf`: `try_files $uri /index.html` für SPA-Routing, Assets-Cache 1y
- `frontend/.dockerignore`: node_modules, dist, .env*, playwright-report ausgeschlossen
- `docker-compose.yml`: backend (Port 8000, healthcheck via /health) + frontend (Port 5174, depends on backend healthy)
- `.env.example`: CORS_ORIGINS, FRONTEND_PORT ergänzt
- Start: `docker compose up --build` — Migrations laufen automatisch vor dem Backend-Start

### 2026-04-24 — Phase 6, Schritt 2: E2E-Tests (Playwright)

- `tests/e2e/global-setup.ts`: Health-Check gegen `/health`, dann `uv run python -m scripts.seed --reset` (überspringt wenn Backend nicht erreichbar)
- `playwright.config.ts`: `globalSetup` hinzugefügt + `video: "retain-on-failure"`
- `KanbanColumn.tsx`: `data-testid="column-{status}"` auf äußerstem Div
- `KanbanTaskCard.tsx`: `data-testid="task-card-{id}"` auf äußerstem Div
- `tests/e2e/tasks.spec.ts`: 5 Tests — Create via UI, Transition via Actions-Dropdown, Edit Titel, Delete, Validierungs-Error
- `tests/e2e/sprints.spec.ts`: 4 Tests — Create via UI, Kanban-Spalten prüfen, Drag & Drop (review→done, 1800px-Viewport, manuelle Mouse-Steps für dnd-kit), Sprint starten
- `tests/e2e/goals.spec.ts`: 4 Tests — Create via UI, Goal-Detail aufrufen, KeyResult hinzufügen, Goal löschen
- `tests/e2e/dashboard.spec.ts`: 4 Tests — Active Sprint Name, Metrics Widget, Velocity Widget, Goal Progress
- Alle Backend-Tests: via `request`-Fixture direkt gegen `http://localhost:8000`

### 2026-04-24 — Phase 6, Schritt 1: Seed-Daten

- `backend/scripts/__init__.py` + `backend/scripts/seed.py`
- Aufruf: `uv run python -m scripts.seed [--reset]` (aus `/backend`)
- Idempotent via `uuid.uuid5(SEED_NS, name)` — feste UUIDs, `merge()` macht Upsert
- `--reset`: löscht `key_results → tasks → sprints → goals` (FK-Reihenfolge)
- Daten: 4 Sprints (2 completed/19+22 pts, 1 active/28 pts, 1 planned), 31 Tasks (23 sprint, 5 daily, 2 milestone, 1 goal-type), 3 Goals, 7 KeyResults
- Dashboard-Coverage: Velocity zeigt 2 Balken (Ø 20.5 pts), Burndown aktiver Sprint, Goal-Progress 93%/35%/85%
- 449 Backend-Tests weiterhin grün ✅

### 2026-04-24 — Phase 5, Schritt 7: Polish & Smoke-Tests

- `sonner` 2.0.7 + `@playwright/test` 1.59.1 installiert
- `src/components/ui/sonner.tsx`: shadcn-konformer Toaster-Wrapper
- `src/components/ui/skeleton.tsx`: `animate-pulse`-Primitive
- `src/components/shared/ErrorBoundary.tsx`: Class-Component mit "Try again"-Reset
- `App.tsx`: `<Toaster />` eingebunden
- `AppLayout.tsx`: `<ErrorBoundary>` um `<Outlet />` (schützt einzelne Seiten)
- Toast `success/error` in allen Mutations: TaskCreate/Edit/Delete, SprintCreate/Start/Complete/Delete, GoalDelete, KRCreate/Edit/Delete (9 Dateien)
- Skeleton-Loading in TasksPage (5 Zeilen), SprintsPage (3 Cards), GoalsPage (3 Cards)
- `playwright.config.ts`: webServer (`pnpm dev`), Chromium, `reuseExistingServer`
- `tests/e2e/smoke.spec.ts`: 7 Tests — Dashboard/Tasks/Sprints/Goals laden, Sidebar-Navigation, 3 Modal-Open/Close-Flows
- `vitest.config.ts`: `tests/e2e/**` von Vitest-Scan ausgeschlossen
- **69 Unit-Tests, alle grün** | Build sauber ✅
- E2E-Tests mit `pnpm test:e2e` starten (Playwright-Browser-Installation: `pnpm exec playwright install chromium`)

### **Phase 5 vollständig abgeschlossen ✅**

### 2026-04-24 — Phase 5, Schritt 6: Dashboard

- `recharts` 3.8.1 installiert (eigene TS-Types, kein `@types/recharts` nötig)
- `src/api/hooks/dashboard.ts`: 5 Hooks — `useDashboard`, `useMetrics`, `useBurndown(sprintId?)`, `useVelocity(lastN?)`, `useGoalProgress()` — alle mit `refetchInterval: 30_000`
- `MetricsWidget`: Counts-Tabelle + Completion Rate als Donut (Recharts PieChart), leerer Zustand
- `BurndownWidget`: LineChart mit ideal_line (grau, gestrichelt) + ReferenceLine für actual_remaining (grün) + optionale ReferenceLine für heute (blau)
- `VelocityWidget`: BarChart je Sprint + ReferenceLine für average_velocity (gelb, gestrichelt)
- `GoalProgressWidget`: Goal-Liste mit Progressbars + KR-Count, aria-konform
- `DashboardPage`: 2×2-Grid (responsive 1-spaltig), Skeleton-Loader, Burndown-Fehler-Fallback (kein aktiver Sprint)
- 19 neue Tests (MetricsWidget 5, GoalProgressWidget 8, DashboardPage 6)
- **69 Tests total, alle grün** | Build sauber ✅

### 2026-04-24 — Phase 5, Schritt 5: Goals-View

- `src/api/hooks/goals.ts`: alle 9 Hooks (Goal CRUD + KeyResult CRUD)
- GoalsPage: Grid von GoalCards; jede Card fetcht eigene KRs für Fortschritt
- GoalCard: Titel, Prio, KR-Count, Aggregate-Progressbar (aria-konform), Delete
- GoalDetailPage: Overall-Progressbar + KR-Liste + Add/Edit/Delete
- KeyResultItem: Titel, current/target/unit, Progressbar (gecappt bei 100%), Edit/Delete
- KeyResultCreateModal: title + target + current + unit + description
- KeyResultEditModal: current_value aktualisieren
- 10 neue Tests (GoalCard, KeyResultItem mit Progress-/aria-Assertions)
- **50 Tests total, alle grün**

### 2026-04-24 — Phase 5, Schritt 4: Sprint-View & Kanban-Board

- `src/api/hooks/sprints.ts`: useSprints, useActiveSprint, useSprint, useSprintTasks, useCreateSprint, useStartSprint, useCompleteSprint, useDeleteSprint
- SprintsPage: Card-Grid + SprintCreateModal (name + Datumsbereich)
- SprintCard: Name, Datum, Status-Badge, Task-Count, Start/Complete/Delete-Aktionen
- SprintDetailPage: Header + KanbanBoard
- KanbanBoard: DndContext, drag-end → useTransitionTask (optimistisches Update aus Step 3)
- KanbanColumn: Droppable + SortableContext + ScrollArea, farbcodierte Header
- KanbanTaskCard: Sortable, Drag-Overlay, Priority-Dot, Story-Points-Badge
- shadcn card + scroll-area (src/-Import-Bug gefixt)
- **40 Tests, alle grün**

### 2026-04-24 — Phase 5, Schritt 3: Tasks-View

- `src/api/hooks/tasks.ts`: useTasks, useCreateTask, useUpdateTask, useDeleteTask, useTransitionTask (optimistisches Update)
- TasksPage: FilterBar + Tabelle + Create/Edit/Delete Modals
- TaskFilterBar: Status / Priorität / Typ (client-seitig gefiltert)
- TaskTable: shadcn Table mit StatusBadge, PriorityBadge, Actions
- TaskActions: DropdownMenu mit erlaubten Status-Übergängen (TRANSITIONS-Map)
- TaskCreateModal: type-aware (daily/sprint/goal/milestone Felder)
- TaskEditModal: title, description, priority, estimation
- TaskDeleteDialog: AlertDialog
- Fix: shadcn-Komponenten hatten `src/`-Imports statt `@/` — global ersetzt
- **27 Tests, alle grün**

### 2026-04-24 — Phase 5, Schritt 2: Layout & Routing

- React Router v7: 6 Routen unter `AppLayout` (/, /tasks, /sprints, /sprints/:id, /goals, /goals/:id)
- `AppLayout`: Sidebar (240px) mit NavLink + Active-Highlight, Header mit ThemeToggle
- `stores/theme.ts`: Zustand-Store mit localStorage-Persistenz; setzt `dark`-Klasse auf `<html>`
- Dark Mode: CSS-Variablen in `index.css` + `@custom-variant dark (&:is(.dark *))`
- shadcn `button`, `separator`, `badge` installiert — `components.json` auf `src/`-Pfade korrigiert
- Fix: TypeScript 6 `erasableSyntaxOnly` — Constructor-Parameter-Properties entfernt
- 3 AppLayout-Tests — **12 Tests total, alle grün**

### 2026-04-24 — Phase 5, Schritt 1: API-Anbindung & Type-Generierung

- `openapi-typescript` → `pnpm generate-api-types` aus `backend/openapi.json`
- `src/api/types.ts` generiert (1746 Zeilen, alle Endpoints abgedeckt)
- `src/api/client.ts`: fetch-Wrapper (`ApiError`, `apiGet/Post/Patch/Delete`)
- `src/api/hooks/`: Shell-Dateien für tasks, sprints, goals, dashboard
- Vitest + jsdom + @testing-library/react konfiguriert (`vitest.config.ts`, `test-setup.ts`)
- 9 Tests für client.ts (Happy Path + Error-Handling)
- `react-router-dom` installiert (wird in Schritt 2 verdrahtet)
- `.env.local` + `.env.example` mit `VITE_API_URL`

### 2026-04-23 — Phase 4: Fehlende Endpoints + OpenAPI-Refresh

**Lücke 1:** `GET /sprints/{sprint_id}/tasks` (mit optionalem `?status=`-Filter)
- In `sprint_router.py` ergänzt (trivial read + status-filter → direkter Repo-Aufruf)
- 8 neue API-Tests

**Lücke 2:** 4 Dashboard-Sub-Endpoints
- `GET /dashboard/metrics` → Zähler + completion_rate (excl. Cancelled)
- `GET /dashboard/burndown` → ideale Linie (linear) + actual_remaining; optional `?sprint_id=`
- `GET /dashboard/velocity` → done story_points je completed Sprint + Durchschnitt; `?last_n=5`
- `GET /dashboard/goal-progress` → avg KR-Fortschritt je Ziel
- 4 neue Use Cases (allesamt Berechnungs-Logik → Use Cases, nicht Router)
- 27 neue Use-Case-Tests + 18 neue API-Tests

**Lücke 3:** `GET /goals/{goal_id}/key-results/{kr_id}` (Single-KR-Fetch)
- Trivial read → direkter Repo-Aufruf in `goal_router.py`
- 2 neue API-Tests

**openapi.json** neu exportiert (alle Endpunkte enthalten)
**449 Tests passing** (77 neue in dieser Teilsession)

### 2026-04-24 — Phase 4: Architektur-Review-Fixes

**Verstoss 1 — Router → Use Cases:**
- `UpdateSprintUseCase` + `DeleteSprintUseCase` (aktiver Sprint → 409 + SprintDeletedEvent)
- `GetDashboardUseCase` (Aggregations-Logik aus Router extrahiert)
- `DeleteTaskUseCase`, `DeleteGoalUseCase`, `DeleteKeyResultUseCase` + je ein Delete-Event
- 4 neue Delete-Events: TaskDeletedEvent, SprintDeletedEvent, GoalDeletedEvent, KeyResultDeletedEvent

**Verstoss 2 — DI auf Interfaces:**
- `dependencies.py`: Return-Typen + Annotated-Aliases auf ITaskRepository / ISprintRepository / IGoalRepository / IEventBus

**Dokumentation:**
- `CLAUDE.md`: Repo-Regel ergänzt
- `Excalidraw/design-decisions.md`: neu angelegt (Löschregeln, Use-Case-Regel, DI-Entscheidung)
- **367 Tests passing** (14 neue)

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
