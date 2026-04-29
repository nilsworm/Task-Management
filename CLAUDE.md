# CLAUDE.md — Personal Task Management System

Diese Datei ist der dauerhafte Kontext für Claude Code. Bei jeder Session zuerst lesen. Für den aktuellen Fortschritt und die nächsten Schritte immer `PROGRESS.md` prüfen.

---

## Projektüberblick

Personal Task Management System, ähnlich zu Azure DevOps / Jira, aber für einen einzelnen Nutzer. Kein Multi-User, keine kollaborativen Features. Das System wird auf einem **eigenen Hetzner-Server via Coolify** deployt und ist damit über das öffentliche Internet erreichbar — Security ist deshalb kein Nice-to-have, sondern Pflicht ab Tag eins.

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
- PostgreSQL 16 via Docker Compose (lokal) bzw. als verwalteter Service in Coolify (Produktion)
- pgAdmin lokal zugänglich, in Produktion **nicht** öffentlich exponieren
- Monorepo-Struktur (`/backend`, `/frontend`)
- **Deployment-Ziel:** Hetzner-Server (Cloud oder dedicated) mit Coolify als PaaS-Layer
- Reverse Proxy + TLS-Terminierung via Coolify (Traefik) mit Let's Encrypt

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

## Security (verbindlich, nicht verhandelbar)

Da das System öffentlich erreichbar deployt wird, gelten Security-Anforderungen ab dem ersten Commit. Security wird nicht "später nachgezogen".

**Authentifizierung & Zugriff:**
- Auch wenn es ein Single-User-System ist: Der Zugang muss durch ein robustes Auth-Verfahren geschützt sein (z. B. Session-Cookie nach Login mit starkem Passwort + Argon2id, optional zusätzlich TOTP). Kein offener Endpoint, kein "ist ja nur ich".
- Session-Cookies: `HttpOnly`, `Secure`, `SameSite=Strict`, kurze Lifetime + Refresh-Mechanik.
- Rate-Limiting auf Auth-Endpoints (Login, Passwort-Reset) — z. B. via `slowapi` oder Reverse-Proxy-Ebene.

**Transport & Netzwerk:**
- Ausschließlich HTTPS, HSTS aktiv, kein Mixed Content.
- CORS strikt konfiguriert: nur die eigene Frontend-Domain, keine Wildcards.
- Security-Header gesetzt: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` minimal.
- Datenbank, pgAdmin und interne Services **nie** öffentlich exponieren — nur via Coolify-internes Netzwerk oder SSH-Tunnel.

**Eingaben & Daten:**
- Alle Eingaben über Pydantic-Schemas validieren. Keine Roh-Strings in SQL — SQLAlchemy-ORM oder Parameter-Binding.
- Keine Geheimnisse im Code oder in Git. `.env`-Variablen werden in Coolify als Secrets gepflegt, lokal über `.env` (in `.gitignore`).
- Backups der Datenbank verschlüsselt ablegen, Restore-Prozedur dokumentieren.

**Abhängigkeiten & Build:**
- Dependencies regelmäßig aktualisieren (`uv` Lockfile, `pnpm` Lockfile committen).
- Vulnerability-Scans: `pip-audit` / `pnpm audit` als Teil von CI.
- Docker-Images: schlanke Base-Images (z. B. `python:3.12-slim`), als Non-Root-User laufen lassen, nur benötigte Ports exponieren.

**Logging & Fehler:**
- Keine sensiblen Daten (Passwörter, Tokens, Cookies) in Logs.
- Fehlermeldungen an den Client sind generisch, Details bleiben im Server-Log.
- Audit-Log für sicherheitsrelevante Events (Login, Login-Fehler, Passwort-Änderung).

Bei jeder neuen Funktion: kurz prüfen, welche Security-Implikationen sie hat (Input-Validation, AuthZ, Logging). Steht sicherheitsrelevantes Verhalten zur Diskussion, **vorher Rücksprache** halten.

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

## Denken vor dem Coden — Simplicity First

Claude Code soll **erst nachdenken, dann coden**. Tempo entsteht nicht durch schnelles Tippen, sondern durch das Vermeiden falscher Abzweigungen.

**Vor jeder Implementierung:**
1. Problem in eigenen Worten zusammenfassen.
2. Die einfachste Lösung skizzieren, die das Problem tatsächlich löst — nicht die eleganteste, nicht die generischste.
3. Prüfen: Gibt es schon Code/Pattern im Projekt, der wiederverwendet werden kann?
4. Erst dann einen kurzen Plan vorschlagen und auf Freigabe warten.

**Simplicity-Leitlinien:**
- **YAGNI:** Keine Funktion, kein Feld, keine Abstraktion ohne konkreten aktuellen Bedarf. Spekulative Flexibilität ist Schulden.
- **KISS:** Die offensichtliche Lösung ist meistens die richtige. Cleverness rechtfertigen müssen, nicht Einfachheit.
- **Boring Tech wins:** Bekannte, langweilige Lösungen vor neuen, glänzenden. Kein neues Lib-/Pattern-Experiment, ohne dass ein Problem es wirklich erzwingt.
- **Erst eine Schicht, nicht drei:** Lieber zuerst eine konkrete Implementierung schreiben und beim zweiten ähnlichen Fall abstrahieren — nicht beim ersten.
- **Wenig Code > viel Code:** Jede Zeile ist Wartungslast. Wenn etwas weggelassen werden kann, weglassen.
- **Deutliche Grenzen statt clevere Generik:** Kleine, klar geschnittene Module sind besser als ein generisches Framework, das alles könnte.

**Eskalation:** Wenn eine Aufgabe Komplexität erzwingen würde, die nicht durch den aktuellen Bedarf gedeckt ist — **stoppen und nachfragen**, statt vorausschauend "auf Verdacht" zu bauen.

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
2. Erst nachdenken (siehe "Simplicity First"), dann einen kurzen Plan vorschlagen, auf Freigabe warten, dann umsetzen
3. Nach jeder abgeschlossenen Teilaufgabe `PROGRESS.md` aktualisieren (Checkboxen + Session-Log)
4. Bei Unklarheiten nachfragen, nicht raten

**Nie:**
- Security-Vorgaben aufweichen oder "für später" verschieben
- Cloud-spezifische Services nutzen, die nicht zu Hetzner/Coolify passen (Vendor-Lock-in vermeiden)
- Die in den Excalidraw-Dateien definierte Architektur eigenmächtig umstrukturieren — bei Bedarf vorher Rücksprache
- Mehrere Phasen in einer Session mischen
- Große Datei-Rewrites, wenn ein gezielter `Edit` reicht
- Komplexität auf Verdacht einbauen ("könnte man später brauchen")

**Commits:**
- Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)
- Pro Commit ein abgeschlossener Schritt, kein "WIP"-Brei
- Commit-Message in Englisch

---

## Deployment

**Lokal (Entwicklung):**
- `docker compose up` startet Postgres + pgAdmin
- Backend und Frontend laufen lokal über `uv run` bzw. `pnpm dev`

**Produktion (Hetzner + Coolify):**
- Coolify verwaltet Build & Deploy aus dem Git-Repo (Self-hosted PaaS auf Hetzner-Server).
- Backend und Frontend werden als getrennte Coolify-Services deployt, jeweils mit eigenem Dockerfile.
- Postgres läuft als Coolify-managed Service, **nicht** öffentlich erreichbar.
- Secrets (DB-URL, Session-Secret, etc.) ausschließlich über Coolifys Environment-Variable-Mechanismus, niemals im Repo.
- Reverse Proxy (Traefik in Coolify) erledigt TLS via Let's Encrypt.
- Deployment-relevante Konfiguration (Dockerfiles, Healthchecks, Migrations-Run) gehört ins Repo, nicht in Coolifys UI-Konfiguration alleine — Reproduzierbarkeit hat Vorrang.

---

## Projektstruktur

```
/
├── CLAUDE.md              # Diese Datei
├── PROGRESS.md            # Aktueller Stand und Phasenplan
├── README.md              # Setup-Anleitung
├── docker-compose.yml     # Postgres + pgAdmin (lokal)
├── .env.example
├── .gitignore
├── /Excalidraw            # Architektur-Diagramme
│   ├── class-diagram.excalidraw
│   ├── architecture-overview.excalidraw
│   └── design-decisions.md
├── /backend
│   ├── pyproject.toml
│   ├── Dockerfile
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
    ├── Dockerfile
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
- Multi-User-Funktionalität, Teams, Rollen, geteilte Workspaces

Wenn ein Feature "nice to have" ist, gehört es in `PROGRESS.md` unter "Backlog" — nicht in die aktuelle Phase.
