# CSV Import Endpoint — Design Spec
**Date:** 2026-05-17  
**Branch:** `feature/csv-import-endpoint`  
**Status:** Approved

---

## Kontext

Die Consorsbank-CSV wird per Mac Shortcuts automatisch an `POST /cost/import` geschickt, sobald sie heruntergeladen wurde. Der bisherige `ImportScheduler` (wöchentlicher APScheduler-Job, Ordner-Scanning) wird vollständig entfernt, da er durch diesen Workflow obsolet ist.

---

## Scope

### Neu
- `ICostRepository.transaction_exists(date, amount, description) -> bool`
- `PostgresCostRepository.transaction_exists()` — EXISTS-Query
- `InMemoryCostRepository.transaction_exists()` — Implementierung (iteriert über In-Memory-Liste)
- `ImportTransactionsUseCase` in `cost_use_cases.py`
- `POST /cost/import` in `cost_router.py`

### Entfernt
- `src/application/services/import_scheduler.py`
- `tests/application/test_import_scheduler.py`
- APScheduler-Dependency (`apscheduler` in `pyproject.toml`)
- `start_scheduler()` / `stop_scheduler()` + alle Scheduler-Imports aus `main.py`
- `IMPORT_FOLDER` aus `config.py` und `.env.example`
- Volume-Mount `./imports:/app/imports` aus `docker-compose.yml`
- `GET /cost/import-status` Endpoint
- `src/features/cost/ImportStatusCard.tsx` + zugehöriger Test
- `useImportStatus()` Hook aus `src/api/hooks/cost.ts` + zugehöriger Test

### Unverändert
- `CSVParser` (parse_consorsbank, parse_trade_republic)
- `create_transaction_from_import()` Repository-Methode

---

## Architektur

Das Projekt folgt **Clean Architecture / DDD**. Dependency-Richtung immer nach innen:

```
Presentation (Router) → Application (Use Case) → Domain (Interface) ← Infrastructure (Repo)
```

**Regeln die einzuhalten sind:**
- Kein Framework-Import (FastAPI, SQLAlchemy) im Use Case oder Domain-Layer
- Use Case kennt nur `ICostRepository`, nie `PostgresCostRepository`
- Keine Business-Logik (Dedup-Prüfung) im Router oder Repository
- Repository macht ausschließlich Datenzugriff — kein Entscheidungs-Logik

---

## Use Case: `ImportTransactionsUseCase`

**Datei:** `src/application/use_cases/cost_use_cases.py`

```python
@dataclass
class ImportTransactionsInput:
    parsed_rows: list[dict]   # [{date, amount, description, type}]
    import_source: str        # "consorsbank" | "trade_republic"

@dataclass
class ImportTransactionsResult:
    imported: int
    skipped: int
```

**Logik:**
1. Für jede Zeile in `parsed_rows`: `cost_repo.transaction_exists(date, amount, description)`
2. Existiert → `skipped += 1`, weiter
3. Existiert nicht → `cost_repo.create_transaction_from_import(row, import_source)`, `imported += 1`
4. Gibt `ImportTransactionsResult` zurück

**Fehlerbehandlung:** Einzelne Zeilen-Fehler werden geloggt und übersprungen (graceful degradation, konsistent mit bisherigem Verhalten).

---

## Repository: `transaction_exists()`

**Interface (`ICostRepository`):**
```python
async def transaction_exists(self, date: date, amount: Decimal, description: str) -> bool: ...
```

**Postgres-Implementierung:**
- Single `EXISTS`-Query auf `cost_transactions` mit Filter `(date = :date AND amount = :amount AND description = :description)`
- Gibt `True` / `False` zurück

**InMemory-Stub:**
- Iteriert über `self._transactions`, prüft gleiche drei Felder

---

## Endpoint: `POST /cost/import`

**Router:** `src/api/routers/cost_router.py`

**Request:** `multipart/form-data`, Feld `file: UploadFile`

**Format-Erkennung aus Dateiname:**
- `"consorsbank"` im Namen (case-insensitive) → `CSVParser.parse_consorsbank()`
- `"trade_republic"` oder `"traderepublic"` im Namen → `CSVParser.parse_trade_republic()`
- Kein Match → `400 Bad Request`: `{"detail": "Unbekanntes CSV-Format. Dateiname muss 'consorsbank' oder 'trade_republic' enthalten."}`

**Temp-File-Handling:**
```python
with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
    content = await file.read()
    tmp.write(content)
    tmp_path = Path(tmp.name)
try:
    parsed_rows = CSVParser.parse_consorsbank(tmp_path)
finally:
    tmp_path.unlink(missing_ok=True)
```

**Parse-Fehler (`InvalidCSVFormatError`, `InvalidTransactionDataError`):**
→ `400 Bad Request` mit Fehlerdetail

**Erfolg:**
→ `200 OK`: `{"imported": N, "skipped": M}`

---

## Tests

### Backend — Use Case (`tests/application/test_cost_use_cases.py`)

| Test | Beschreibung |
|------|-------------|
| `test_import_transactions_all_new` | Alle Zeilen neu → `imported: N, skipped: 0` |
| `test_import_transactions_all_duplicates` | Alle Zeilen existieren → `imported: 0, skipped: N` |
| `test_import_transactions_mixed` | Teils neu, teils Duplikat → korrekte Counts |
| `test_import_transactions_empty` | Leere Liste → `imported: 0, skipped: 0` |

Verwenden `InMemoryCostRepository` — kein I/O.

### Backend — API (`tests/api/test_cost_router.py`)

| Test | Beschreibung |
|------|-------------|
| `test_import_consorsbank_csv` | Gültige Consorsbank-CSV → 200, korrekte Counts |
| `test_import_trade_republic_csv` | Gültige Trade Republic-CSV → 200 |
| `test_import_unknown_filename` | `unknown.csv` → 400 |
| `test_import_malformed_csv` | Datei mit falschen Spalten → 400 |
| `test_import_duplicate_skipped` | Zweiter Upload gleicher CSV → `skipped: N, imported: 0` |

### Backend — Repository (`tests/infrastructure/test_cost_repository.py`)

| Test | Beschreibung |
|------|-------------|
| `test_transaction_exists_true` | Existierende Transaktion → True |
| `test_transaction_exists_false` | Nicht-existierende → False |

### Frontend — Gelöscht

- `ImportStatusCard`-Tests werden gelöscht
- `useImportStatus`-Tests werden gelöscht

---

## Infrastruktur

### Neuer Branch
```bash
git checkout -b feature/csv-import-endpoint
```

### `.gitignore`
```
imports/
```
Eintrag hinzufügen (falls lokaler `/imports`-Ordner noch existiert).

### `docker-compose.yml`
Volume-Mount `./imports:/app/imports` entfernen.

### `docker-compose.prod.yml`
Kein Import-Folder-Mount benötigt (war nie drin).

### OpenAPI + TypeScript-Types
Nach Endpoint-Implementierung:
```bash
cd backend && uv run python -m scripts.export_openapi
cd frontend && pnpm generate-api-types
```

---

## Nicht im Scope

- Frontend-Upload-Dialog (nicht nötig — Mac Shortcuts übernimmt den Upload)
- Automatisierungsscript für Mac Shortcuts (liegt beim User)
- Authentifizierung am Endpoint (liegt bei Traefik Basic Auth)
- Tag-Kategorisierung / ML-Klassifizierung
