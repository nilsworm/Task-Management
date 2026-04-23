# CLAUDE.md — Personal Task Management System

Diese Datei ist der dauerhafte Kontext für Claude Code. Bei jeder Session zuerst lesen. Für den aktuellen Fortschritt und die nächsten Schritte immer `PROGRESS.md` prüfen.

---

## Projektüberblick

Personal Task Management System, ähnlich zu Azure DevOps / Jira, aber für einen einzelnen Nutzer und ausschließlich lokal. Kein Multi-User, keine Authentication, keine Cloud-Deployment-Anforderungen.

**Kernfunktionen:**
- Task-Management mit Priorität, Aufwandsschätzung, Tags, State Machine
- Planung auf drei Ebenen: Daily, Sprint (2 Wochen), Monthly
- Langfristige Ziele als OKRs (Objective + KeyResults)
- Dashboards mit Metriken (Burndown, Velocity, Completion Rate)

---

## Tech-Stack (verbindlich)

**Backend:**
- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (async)
- Alembic für Migrations
- Pydantic v2
- pytest + httpx für Tests
- uv als Dependency Manager

**Frontend:**
- TypeScript (strict mode)
- Vite + React 18+
- TanStack Query für Server-State
- Zustand für Client-State
- Tailwind CSS + shadcn/ui
- Recharts für Dashboards
- openapi-typescript für Type-Generierung aus OpenAPI
- pnpm als Package Manager
- Vitest (Unit) + Playwright (E2E)

**Infrastruktur:**
- PostgreSQL 16 via Docker Compose
- pgAdmin lokal zugänglich
- Monorepo-Struktur (`/backend`, `/frontend`)

Keine Alternativen vorschlagen, solange der Stack nicht explizit hinterfragt wird.

---

## Architektur

Das Projekt folgt **Clean Architecture** und **Domain-Driven Design**.

**Layer (Dependency-Richtung nach innen):**
1. Presentation (FastAPI-Router, Frontend)
2. Application (Use Cases, Services)
3. Domain (Entities, Value Objects, Domain Events, Interfaces)
4. Infrastructure (SQLAlchemy-Models, Repositories, Event-Bus)

**Architektur-Artefakte:**
- `/Excalidraw/class-diagram.excalidraw` — Klassendiagramm
- `/Excalidraw/architecture-overview.excalidraw` — Layer-Übersicht
- `/Excalidraw/design-decisions.md` — Begründungen

**WICHTIG beim Lesen der Excalidraw-Dateien:** Nutze `Grep` mit gezielten Suchen nach Klassennamen, nicht `Read` auf die ganze Datei — die JSON-Struktur kostet sonst unnötig Tokens.

**Verwendete Patterns:**
- State Pattern für Task-Zustandsübergänge
- Strategy Pattern für Planning (Daily/Sprint/Monthly)
- Repository Pattern für Persistenz
- Factory Pattern für Task-Erstellung
- Observer / Event-Bus für Domain Events

---

## Code-Konventionen

**Python:**
- Type-Hints durchgehend (mypy-kompatibel)
- Async-first für alles, was I/O macht
- Pydantic v2 für DTOs, SQLAlchemy-Models streng von Domain-Entities trennen
- Docstrings nur da, wo der Zweck nicht aus Namen + Typen hervorgeht
- Keine Business-Logik in Routern oder SQLAlchemy-Models — nur in Domain oder Application-Layer
- Repositories machen ausschließlich Datenzugriff. Keine Domain-Regeln, keine Berechnungen, keine Berechtigungen in Repos. Sobald solche Logik anfällt, entsteht ein Use Case. Triviale CRUD-Reads bleiben direkter Repo-Zugriff aus dem Router.

**TypeScript:**
- Strict Mode ohne Ausnahmen
- `any` ist verboten, außer mit einer Zeile Kommentar-Begründung
- Funktionale Komponenten, keine Class Components
- Types aus OpenAPI generieren, nicht manuell nachbauen
- shadcn/ui-Komponenten bevorzugen, bevor neue gebaut werden

**Allgemein:**
- Sprechende Namen statt Kommentare
- Kleine Dateien, klare Zuständigkeiten
- Tests in gleicher Ordnerstruktur wie Source (`tests/` spiegelt `src/`)

---

## Testing

- **Domain-Layer:** 100 % Unit-Test-Coverage Ziel (pure Logic, leicht testbar)
- **Application-Layer:** Use Cases mit Mock-Repositories testen
- **Infrastructure:** Integration-Tests mit echter Postgres (Testcontainers oder separates Test-Schema)
- **API:** httpx-basierte Tests gegen FastAPI-TestClient
- **Frontend:** Vitest für Komponenten/Hooks, Playwright für kritische User-Flows

Tests werden **parallel zur Implementierung** geschrieben, nicht nachgelagert.

---

## Arbeitsweise mit Claude Code

**Immer:**
1. Zu Beginn jeder Session `PROGRESS.md` lesen
2. Erst einen kurzen Plan vorschlagen, auf Freigabe warten, dann umsetzen
3. Nach jeder abgeschlossenen Teilaufgabe `PROGRESS.md` aktualisieren (Checkboxen + Session-Log)
4. Bei Unklarheiten nachfragen, nicht raten

**Nie:**
- Authentication, User-Management, Multi-Tenancy einführen
- Cloud-spezifische Services nutzen (alles muss lokal laufen)
- Die in den Excalidraw-Dateien definierte Architektur eigenmächtig umstrukturieren — bei Bedarf vorher Rücksprache
- Mehrere Phasen in einer Session mischen
- Große Datei-Rewrites, wenn ein gezielter `Edit` reicht

**Commits:**
- Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)
- Pro Commit ein abgeschlossener Schritt, kein "WIP"-Brei
- Commit-Message in Englisch

---

## Projektstruktur

```
/
├── CLAUDE.md              # Diese Datei
├── PROGRESS.md            # Aktueller Stand und Phasenplan
├── README.md              # Setup-Anleitung
├── docker-compose.yml     # Postgres + pgAdmin
├── .env.example
├── .gitignore
├── /Excalidraw            # Architektur-Diagramme
│   ├── class-diagram.excalidraw
│   ├── architecture-overview.excalidraw
│   └── design-decisions.md
├── /backend
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── /alembic
│   ├── /src
│   │   ├── /domain
│   │   ├── /application
│   │   ├── /infrastructure
│   │   └── /api
│   └── /tests
└── /frontend
    ├── package.json
    ├── vite.config.ts
    ├── /src
    │   ├── /components
    │   ├── /features      # Feature-basiert organisiert
    │   ├── /lib
    │   ├── /api           # generierte Types + Client
    │   └── /routes
    └── /tests
```

---

## Scope-Disziplin

Es ist ein Feierabend-Projekt, nicht Jira. Features, die **nicht** Teil des Scopes sind, solange nicht explizit angefragt:

- Mobile-App / PWA-Installation
- Echtzeit-Kollaboration / WebSockets
- Benachrichtigungen / E-Mail-Versand
- Kalender-Sync, Git-Integration, externe APIs
- Theme-System jenseits von Light/Dark

Wenn ein Feature "nice to have" ist, gehört es in `PROGRESS.md` unter "Backlog" — nicht in die aktuelle Phase.