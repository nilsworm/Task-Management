# CSV Import für Finanz-Automation — Design-Spec

**Datum:** 2026-05-14  
**Status:** Design-Approved, Implementation-Pending

---

## Overview

Automatisierter wöchentlicher Import von Bank-Transaktionen via CSV-Dateien. Das System überwacht einen lokalen Folder (`/imports`), parst neue CSVs von Consorsbank und Trade Republic, und speichert die Transaktionen im Cost-Management-Modul. Intelligente Kategorisierung (Tags) ist **Phase 2**.

**Scope dieser Phase:**
- CSV-Parsing (Consorsbank + Trade Republic Format)
- Wöchentliches Scheduling
- Archivierung nach erfolgreichem Import
- Basic UI-Status

**Out of Scope (Phase 2+):**
- Intelligente Tag-Kategorisierung / ML-Vorschläge
- Duplikat-Erkennung
- Retry-Logic / Import-Fehler-Tracking
- Web-basiertes Upload-UI

---

## Architecture

### Backend

#### 1. CSVParser (Utility-Klasse)

**Datei:** `src/infrastructure/import/csv_parser.py`

```python
class CSVParser:
    @staticmethod
    def parse_consorsbank(file_path: Path) -> list[dict]:
        """Parse Consorsbank CSV export.
        
        Expected columns: Buchungstag, Wertstellung, Umsatzart, Begünstigter / Auftraggeber,
                         Verwendungszweck, Betrag, Saldo
        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": INCOME|EXPENSE}]
        """
        ...

    @staticmethod
    def parse_trade_republic(file_path: Path) -> list[dict]:
        """Parse Trade Republic CSV (converted via kontoauszug.jonathanpagel.com).
        
        Expected columns: Datum, Beschreibung, Typ, Betrag
        Returns: same as above
        """
        ...
```

**Errors:**
- `InvalidCSVFormatError` → wenn erwartete Spalten fehlen
- `InvalidTransactionDataError` → wenn amount/date nicht parsbar ist

---

#### 2. Domain Layer Extension

**File:** `src/domain/entities/transaction.py`

Neues optionales Feld auf `Transaction`:

```python
@dataclass
class Transaction:
    ...
    import_source: str | None = None  # "consorsbank" | "trade_republic" | None
```

Mapper in `infrastructure/persistence/mappers.py` anpassen.

---

#### 3. Repository Extension

**File:** `src/domain/repositories/cost_repository.py`

Neue Methode auf `ICostRepository`:

```python
async def create_transaction_from_import(
    self,
    parsed_row: dict,  # from CSVParser
    import_source: str  # "consorsbank" | "trade_republic"
) -> Transaction:
    """Create and persist a Transaction from parsed CSV row.
    
    Sets import_source for audit trail.
    """
```

**Implementation in PostgresCostRepository:**
- Erstellt `Transaction`-Entity
- Setzt `import_source`
- Speichert via `save_transaction()`

---

#### 4. ImportScheduler (Application Service)

**File:** `src/application/services/import_scheduler.py`

```python
class ImportScheduler:
    def __init__(self, cost_repo: ICostRepository):
        self.cost_repo = cost_repo
        self.import_folder = Path(settings.import_folder)  # /app/imports
        self.archive_folder = self.import_folder / "archived"
    
    async def run_weekly_import(self) -> dict:
        """
        Scan /imports for CSVs, parse, import, archive.
        
        Returns: {"status": "success", "imported": 5, "files": ["consorsbank_...csv"]}
        """
        # Find .csv files (excluding archived/)
        # Detect format: filename pattern → "consorsbank" or "trade_republic"
        # Parse via CSVParser
        # For each row: create_transaction_from_import()
        # Move file to /archived/
        # Return summary
```

**Error Handling:**
- Unparseable CSV → log error, **don't** move file (stays in `/imports` for manual review)
- Individual row error → log, skip row, continue with rest of file
- Invalid amount/date → skip row, continue

**No retry logic, no import_jobs table — keep it simple.**

---

#### 5. Scheduler Registration

**File:** `src/main.py`

Bei App-Startup:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@app.on_event("startup")
async def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        func=import_scheduler.run_weekly_import,
        trigger="cron",
        day_of_week="0",  # Monday
        hour=9,
        minute=0,
        id="weekly_import"
    )
    scheduler.start()
```

**Or separate as background task** (depends on existing pattern in codebase).

---

### Frontend

#### CostManagementPage Extension

**File:** `src/features/cost/CostManagementPage.tsx`

Neue Card in der UI (oben, nach SummaryCards):

```tsx
<ImportStatusCard>
  Last import: May 14, 2026 · 5 transactions
  Import folder: /imports
</ImportStatusCard>
```

**Data Source:**
- New hook: `useImportStatus()` → `GET /cost/import-status`
- Returns: `{ last_import_date: ISO, transaction_count: number }`

**Behavior:**
- Status read-only (kein "Import jetzt"-Button — wöchentlicher Scheduler macht das)
- Aktualisiert bei Page-Load (via TanStack Query)

---

### Infrastructure & Config

#### Docker

**docker-compose.yml:**

```yaml
services:
  backend:
    volumes:
      - ./imports:/app/imports  # CSV import folder
```

**Dockerfile:**
- `apscheduler` in `pyproject.toml` hinzufügen

#### Environment

**.env.example:**

```
IMPORT_FOLDER=/app/imports
```

**config.py:**

```python
import_folder: str = Field(default="/app/imports")
```

---

## Data Flow

```
Week 1:
  User exports Consorsbank CSV → ~/Downloads/consorsbank_2026-05-14.csv
  User copies to ./imports/ folder (locally or via scp/rsync to server)
  
Monday 9:00 AM:
  ImportScheduler triggers
  Finds consorsbank_2026-05-14.csv
  CSVParser.parse_consorsbank() → [{date, amount, desc, type}, ...]
  For each row: create_transaction_from_import()
  Moves file to ./imports/archived/consorsbank_2026-05-14.csv
  
CostManagementPage:
  useImportStatus() fetches last import date + count
  Shows "Last import: May 14 · 5 transactions"
```

---

## Testing Strategy

**Backend:**

1. **Unit Tests (domain/application):**
   - `CSVParser.parse_consorsbank()` – valid file, missing column, malformed row
   - `CSVParser.parse_trade_republic()` – valid file, invalid amount
   - `ImportScheduler.run_weekly_import()` – happy path, archive logic, error handling

2. **Integration Tests (infrastructure):**
   - Full flow: write CSV to temp folder → run scheduler → check DB + archived file
   - Verify `import_source` field set correctly

3. **API Tests:**
   - `GET /cost/import-status` – returns last_import_date + count

**Frontend:**

- `ImportStatusCard` renders correctly with date + count
- `useImportStatus()` hook fetches and displays data

---

## Rollout Plan

**Phase 1 (this sprint):**
- Implement CSVParser + ImportScheduler
- Extend `Transaction` + Repository
- Register scheduler in FastAPI startup
- Add `GET /cost/import-status` endpoint
- Tests for above

**Phase 2 (future):**
- Intelligent tag categorization (rule engine)
- Duplicate detection (transaction hashes)
- Error UI / import logs
- Web-based import history / reruns

---

## Assumptions & Constraints

- CSV files are manually copied to `/imports` (no automated sync from cloud)
- Scheduler runs once per week; exact time is configurable (default Monday 9am)
- Errors in individual rows don't stop the entire file (graceful degradation)
- No undo / re-import of archived files (intentional — keep it simple)
- Trade Republic CSVs are pre-converted via [kontoauszug.jonathanpagel.com](https://kontoauszug.jonathanpagel.com) (user responsibility)

---

## Success Criteria

- ✅ CSVs in `/imports` are parsed and imported weekly without manual intervention
- ✅ Imported transactions appear in CostManagementPage with correct date/amount/type
- ✅ `import_source` field populated for audit trail
- ✅ Parsed files move to `/archived/` after success
- ✅ Unparseable files stay in `/imports/` for manual review
- ✅ UI shows last import status (date + count)
- ✅ Works identically in local Docker + production server
