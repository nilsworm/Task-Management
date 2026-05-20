# CSV Import Endpoint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ersetze den wöchentlichen ImportScheduler durch einen `POST /cost/import`-Endpoint, der CSV-Dateien von Mac Shortcuts entgegennimmt, Duplikate silently überspringt und nur neue Transaktionen persistiert.

**Architecture:** Clean Architecture — Use Case für Dedup-Logik, Repository-Interface für `transaction_exists()`, Router nur für HTTP-Handling. Kein Business-Logic im Router.

**Tech Stack:** Python 3.12, FastAPI `UploadFile`, SQLAlchemy async EXISTS-Query, `tempfile` für Datei-Handling, Pydantic v2, pytest-asyncio.

---

## File Map

| Aktion | Datei |
|--------|-------|
| Modify | `backend/src/domain/cost/repository.py` |
| Modify | `backend/src/infrastructure/persistence/repositories/cost_repository.py` |
| Modify | `backend/src/application/use_cases/cost_use_cases.py` |
| Modify | `backend/src/api/routers/cost_router.py` |
| Modify | `backend/src/main.py` |
| Modify | `backend/src/config.py` |
| Modify | `backend/pyproject.toml` |
| Modify | `docker-compose.yml` |
| Modify | `.gitignore` |
| Modify | `.env.example` |
| Delete | `backend/src/application/services/import_scheduler.py` |
| Delete | `backend/tests/application/test_import_scheduler.py` |
| Modify | `backend/tests/application/test_cost_use_cases.py` |
| Modify | `backend/tests/api/test_cost_router.py` |
| Modify | `backend/tests/infrastructure/test_cost_repository.py` |
| Delete | `frontend/src/features/cost/ImportStatusCard.tsx` |
| Delete | `frontend/src/features/cost/__tests__/ImportStatusCard.test.tsx` |
| Modify | `frontend/src/api/hooks/cost.ts` |
| Modify | `frontend/src/api/__tests__/hooks.cost.test.tsx` |
| Modify | `frontend/src/features/cost/CostManagementPage.tsx` |

---

## Task 1: Branch erstellen + .gitignore

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Branch erstellen**

```bash
cd "/Users/nilsworm/Library/Mobile Documents/com~apple~CloudDocs/Projects/Task Management"
git checkout -b feature/csv-import-endpoint
```

Expected: `Switched to a new branch 'feature/csv-import-endpoint'`

- [ ] **Step 2: `imports/` zu .gitignore hinzufügen**

Öffne `.gitignore` und füge am Ende hinzu:

```
imports/
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add imports/ to .gitignore"
```

---

## Task 2: ImportScheduler entfernen (Backend)

**Files:**
- Delete: `backend/src/application/services/import_scheduler.py`
- Delete: `backend/tests/application/test_import_scheduler.py`
- Modify: `backend/src/main.py`
- Modify: `backend/src/config.py`
- Modify: `backend/pyproject.toml`
- Modify: `docker-compose.yml`
- Modify: `.env.example`

- [ ] **Step 1: Dateien löschen**

```bash
rm "backend/src/application/services/import_scheduler.py"
rm "backend/tests/application/test_import_scheduler.py"
```

- [ ] **Step 2: `main.py` bereinigen**

Ersetze den kompletten Inhalt von `backend/src/main.py` mit:

```python
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import (
    entity_not_found_handler,
    invalid_operation_handler,
    value_error_handler,
)
from src.api.dependencies import get_ollama_client
from src.api.health import router as health_router
from src.api.routers.ai_router import router as ai_router
from src.api.routers.cost_router import router as cost_router
from src.api.routers.dashboard_router import router as dashboard_router
from src.api.routers.goal_router import router as goal_router
from src.api.routers.sprint_router import router as sprint_router
from src.api.routers.task_router import router as task_router
from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Task Manager API",
    version="0.1.0",
    description="Personal task management — single-user, local-only.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)  # type: ignore[arg-type]
app.add_exception_handler(InvalidOperationError, invalid_operation_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]

app.include_router(health_router)
app.include_router(task_router)
app.include_router(sprint_router)
app.include_router(goal_router)
app.include_router(dashboard_router)
app.include_router(cost_router)
app.include_router(ai_router)


@app.on_event("startup")
async def check_ollama() -> None:
    client = get_ollama_client()
    available = await client.is_available()
    if available:
        logger.info("Ollama is available at %s", settings.ollama_base_url)
    else:
        logger.warning(
            "Ollama not reachable at %s — AI endpoints will return 503",
            settings.ollama_base_url,
        )
```

- [ ] **Step 3: `import_folder` aus `config.py` entfernen**

Ersetze in `backend/src/config.py`:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cost_currency: str = "EUR"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    ai_model: str = "meta-llama/llama-3.3-70b-instruct:free"


settings = Settings()
```

- [ ] **Step 4: `apscheduler` aus `pyproject.toml` entfernen**

In `backend/pyproject.toml`, entferne die Zeile:
```
"apscheduler>=3.10.4",
```
aus dem `dependencies`-Array.

- [ ] **Step 5: Volume-Mount aus `docker-compose.yml` entfernen**

In `docker-compose.yml`, entferne folgende zwei Zeilen aus dem `backend`-Service:
```yaml
      IMPORT_FOLDER: /app/imports
```
und
```yaml
      - ./imports:/app/imports
```

- [ ] **Step 6: `IMPORT_FOLDER` aus `.env.example` entfernen**

Entferne die Zeile `IMPORT_FOLDER=...` aus `.env.example` falls vorhanden.

- [ ] **Step 7: `uv sync` ausführen (lockfile updaten)**

```bash
cd backend && uv sync
```

- [ ] **Step 8: Tests laufen lassen**

```bash
cd backend && uv run pytest -x -q
```

Expected: Alle Tests grün. Wichtig: Die 8 gelöschten `test_import_scheduler.py`-Tests fehlen jetzt — das ist korrekt.

- [ ] **Step 9: Commit**

```bash
cd ..
git add backend/src/main.py backend/src/config.py backend/pyproject.toml \
  docker-compose.yml .env.example backend/uv.lock
git commit -m "chore: remove ImportScheduler and APScheduler dependency"
```

---

## Task 3: `GET /cost/import-status` Endpoint entfernen

**Files:**
- Modify: `backend/src/domain/cost/repository.py`
- Modify: `backend/src/infrastructure/persistence/repositories/cost_repository.py`
- Modify: `backend/src/api/routers/cost_router.py`
- Modify: `backend/tests/application/test_cost_use_cases.py`
- Modify: `backend/tests/api/test_cost_router.py`

- [ ] **Step 1: `get_last_import_status` aus `ICostRepository` entfernen**

In `backend/src/domain/cost/repository.py`, lösche folgende Methode komplett:

```python
@abstractmethod
async def get_last_import_status(self) -> dict:
    """Get last import date and transaction count from imports.

    Returns:
        Dict with keys:
            - last_import_date: ISO format date string or None if no imports exist
            - transaction_count: count of transactions with import_source set
    """
    ...
```

- [ ] **Step 2: `get_last_import_status` aus `PostgresCostRepository` entfernen**

In `backend/src/infrastructure/persistence/repositories/cost_repository.py`, lösche die gesamte `get_last_import_status`-Methode (Zeilen 128–142).

- [ ] **Step 3: `get_last_import_status` aus `InMemoryCostRepository` entfernen**

In `backend/tests/application/test_cost_use_cases.py`, lösche die gesamte `get_last_import_status`-Methode (Zeilen 112–126).

- [ ] **Step 4: `GET /cost/import-status` Endpoint aus Router entfernen**

In `backend/src/api/routers/cost_router.py`, lösche:

```python
@router.get("/import-status", response_model=dict)
async def get_import_status(repo: CostRepoDep) -> dict:
    ...
    return await repo.get_last_import_status()
```

- [ ] **Step 5: `test_get_import_status_*` Tests entfernen**

In `backend/tests/api/test_cost_router.py`, lösche den kompletten Block `# GET /cost/import-status` mit allen 4 Tests:
- `test_get_import_status_empty`
- `test_get_import_status_with_imports`
- `test_get_import_status_multiple_imports`
- `test_get_import_status_ignores_manual_transactions`

- [ ] **Step 6: Tests laufen lassen**

```bash
cd backend && uv run pytest -x -q
```

Expected: Alle verbleibenden Tests grün, keine Fehler.

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/cost/repository.py \
  backend/src/infrastructure/persistence/repositories/cost_repository.py \
  backend/src/api/routers/cost_router.py \
  backend/tests/application/test_cost_use_cases.py \
  backend/tests/api/test_cost_router.py
git commit -m "chore: remove GET /cost/import-status endpoint and interface method"
```

---

## Task 4: Frontend ImportStatusCard + useImportStatus entfernen

**Files:**
- Delete: `frontend/src/features/cost/ImportStatusCard.tsx`
- Delete: `frontend/src/features/cost/__tests__/ImportStatusCard.test.tsx`
- Modify: `frontend/src/api/hooks/cost.ts`
- Modify: `frontend/src/api/__tests__/hooks.cost.test.tsx`
- Modify: `frontend/src/features/cost/CostManagementPage.tsx`

- [ ] **Step 1: Dateien löschen**

```bash
rm "frontend/src/features/cost/ImportStatusCard.tsx"
rm "frontend/src/features/cost/__tests__/ImportStatusCard.test.tsx"
```

- [ ] **Step 2: `useImportStatus` aus `cost.ts` entfernen**

In `frontend/src/api/hooks/cost.ts`, lösche:
- Die Konstante `IMPORT_STATUS_KEY`
- Die Funktion `useImportStatus()` (inkl. `export`)
- Den zugehörigen `ImportStatus`-Typ falls dort definiert (sonst in `types.ts` lassen — wird in Task 9 aus der regenerierten OpenAPI entfernt)

- [ ] **Step 3: `useImportStatus`-Tests entfernen**

In `frontend/src/api/__tests__/hooks.cost.test.tsx`, lösche:
- Den `import { useImportStatus }` Import
- Den kompletten `describe("useImportStatus", ...)` Block

- [ ] **Step 4: `ImportStatusCard` aus `CostManagementPage.tsx` entfernen**

In `frontend/src/features/cost/CostManagementPage.tsx`:
- Lösche `import { ImportStatusCard } from "./ImportStatusCard"`
- Lösche `<ImportStatusCard />` aus dem JSX

- [ ] **Step 5: TypeScript + Tests prüfen**

```bash
cd frontend && pnpm tsc --noEmit && pnpm test run
```

Expected: 0 TypeScript-Fehler, alle Tests grün.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/cost/ImportStatusCard.tsx \
  "frontend/src/features/cost/__tests__/ImportStatusCard.test.tsx" \
  frontend/src/api/hooks/cost.ts \
  "frontend/src/api/__tests__/hooks.cost.test.tsx" \
  frontend/src/features/cost/CostManagementPage.tsx
git commit -m "chore: remove ImportStatusCard and useImportStatus hook"
```

---

## Task 5: `transaction_exists()` — Interface + InMemory + Use-Case-Test (TDD)

**Files:**
- Modify: `backend/src/domain/cost/repository.py`
- Modify: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Failing Tests schreiben**

In `backend/tests/application/test_cost_use_cases.py`, füge nach dem letzten Test folgende Tests an:

```python
# ---------------------------------------------------------------------------
# transaction_exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_transaction_exists_returns_true_for_existing(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns True when a transaction with same date/amount/description exists."""
    from datetime import date
    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.expense,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Miete")

    assert result is True


@pytest.mark.asyncio
async def test_transaction_exists_returns_false_for_nonexistent(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns False when no matching transaction exists."""
    from datetime import date

    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Miete")

    assert result is False


@pytest.mark.asyncio
async def test_transaction_exists_requires_all_three_fields(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns False if only date and amount match but description differs."""
    from datetime import date
    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.expense,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Andere Beschreibung")

    assert result is False
```

- [ ] **Step 2: Tests laufen lassen (müssen fehlschlagen)**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_transaction_exists_returns_true_for_existing -v
```

Expected: `FAILED` — `InMemoryCostRepository has no attribute transaction_exists`

- [ ] **Step 3: `transaction_exists` zum Interface hinzufügen**

In `backend/src/domain/cost/repository.py`, füge nach der `get_opening_balance_transaction`-Methode hinzu:

```python
@abstractmethod
async def transaction_exists(
    self, date: "date_type", amount: Decimal, description: str
) -> bool:
    """Check if a transaction with the same date, amount, and description already exists.

    Used for deduplication during CSV import.
    """
    ...
```

Hinweis: `date_type` ist der Python `datetime.date`-Typ. Stelle sicher dass `date` oben importiert ist:
```python
from datetime import date as date_type
```
Falls der Import noch nicht existiert, überprüfe was in `repository.py` bereits importiert ist und passe den Alias an.

- [ ] **Step 4: `transaction_exists` zur `InMemoryCostRepository` hinzufügen**

In `backend/tests/application/test_cost_use_cases.py`, füge in der `InMemoryCostRepository`-Klasse nach `get_opening_balance_transaction` hinzu:

```python
async def transaction_exists(
    self, date: "date_type", amount: Decimal, description: str
) -> bool:
    return any(
        t.date == date and t.amount == amount and t.title == description
        for t in self._transactions.values()
    )
```

Stelle sicher dass `date_type` importiert ist — füge oben hinzu falls nötig:
```python
from datetime import date as date_type
```

- [ ] **Step 5: Tests laufen lassen (müssen grün sein)**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "transaction_exists" -v
```

Expected: 3 × PASSED

- [ ] **Step 6: Alle Tests laufen lassen**

```bash
uv run pytest -x -q
```

Expected: Alle Tests grün.

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/cost/repository.py \
  backend/tests/application/test_cost_use_cases.py
git commit -m "feat: add transaction_exists to ICostRepository and InMemoryCostRepository"
```

---

## Task 6: `transaction_exists()` — PostgresCostRepository + Integration-Test (TDD)

**Files:**
- Modify: `backend/tests/infrastructure/test_cost_repository.py`
- Modify: `backend/src/infrastructure/persistence/repositories/cost_repository.py`

- [ ] **Step 1: Failing Integration-Tests schreiben**

In `backend/tests/infrastructure/test_cost_repository.py`, füge am Ende an:

```python
@pytest.mark.asyncio
async def test_transaction_exists_returns_true(repo: PostgresCostRepository) -> None:
    """transaction_exists returns True for a transaction with matching date/amount/description."""
    from datetime import date
    tx = Transaction.create(
        title="Supermarkt",
        amount=Decimal("45.50"),
        transaction_type=TransactionType.expense,
        transaction_date=date(2026, 5, 10),
    )
    await repo.save_transaction(tx)

    result = await repo.transaction_exists(date(2026, 5, 10), Decimal("45.50"), "Supermarkt")

    assert result is True


@pytest.mark.asyncio
async def test_transaction_exists_returns_false(repo: PostgresCostRepository) -> None:
    """transaction_exists returns False when no matching transaction exists."""
    from datetime import date

    result = await repo.transaction_exists(date(2026, 5, 10), Decimal("45.50"), "Supermarkt")

    assert result is False
```

- [ ] **Step 2: Tests laufen lassen (müssen fehlschlagen)**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_transaction_exists_returns_true -v
```

Expected: `FAILED` — `PostgresCostRepository has no attribute transaction_exists`

- [ ] **Step 3: `transaction_exists` zu `PostgresCostRepository` hinzufügen**

In `backend/src/infrastructure/persistence/repositories/cost_repository.py`, füge nach `get_opening_balance_transaction` hinzu:

```python
async def transaction_exists(
    self, date: "date_type", amount: Decimal, description: str
) -> bool:
    from sqlalchemy import exists as sa_exists
    stmt = select(
        sa_exists().where(
            TransactionModel.date == date,
            TransactionModel.amount == amount,
            TransactionModel.title == description,
        )
    )
    result = await self._session.execute(stmt)
    return bool(result.scalar())
```

Füge oben im File hinzu falls nicht vorhanden:
```python
from datetime import date as date_type
from decimal import Decimal
```

- [ ] **Step 4: Integration-Tests laufen lassen**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py -k "transaction_exists" -v
```

Expected: 2 × PASSED

- [ ] **Step 5: Alle Tests laufen lassen**

```bash
uv run pytest -x -q
```

Expected: Alle Tests grün.

- [ ] **Step 6: Commit**

```bash
git add backend/src/infrastructure/persistence/repositories/cost_repository.py \
  backend/tests/infrastructure/test_cost_repository.py
git commit -m "feat: add transaction_exists to PostgresCostRepository"
```

---

## Task 7: `ImportTransactionsUseCase` (TDD)

**Files:**
- Modify: `backend/tests/application/test_cost_use_cases.py`
- Modify: `backend/src/application/use_cases/cost_use_cases.py`

- [ ] **Step 1: Failing Tests schreiben**

In `backend/tests/application/test_cost_use_cases.py`, füge am Ende an:

```python
# ---------------------------------------------------------------------------
# ImportTransactionsUseCase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_import_transactions_all_new(repo: InMemoryCostRepository) -> None:
    """All rows are new — imported count equals row count, skipped is 0."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("500.00"), "description": "Gehalt", "type": "INCOME"},
        {"date": date(2026, 5, 2), "amount": Decimal("50.00"), "description": "Supermarkt", "type": "EXPENSE"},
    ]
    use_case = ImportTransactionsUseCase(repo)

    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 2
    assert result.skipped == 0
    assert len(repo.transactions) == 2


@pytest.mark.asyncio
async def test_import_transactions_all_duplicates(repo: InMemoryCostRepository) -> None:
    """All rows already exist — imported is 0, skipped equals row count."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("500.00"), "description": "Gehalt", "type": "INCOME"},
    ]
    # Pre-populate repo with the same transaction
    tx = Transaction.create(
        title="Gehalt",
        amount=Decimal("500.00"),
        transaction_type=TransactionType.income,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 0
    assert result.skipped == 1
    assert len(repo.transactions) == 1  # No new transaction added


@pytest.mark.asyncio
async def test_import_transactions_mixed(repo: InMemoryCostRepository) -> None:
    """Mixed rows: some new, some duplicates — counts are accurate."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    # Pre-populate one transaction
    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.expense,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("800.00"), "description": "Miete", "type": "EXPENSE"},  # duplicate
        {"date": date(2026, 5, 3), "amount": Decimal("30.00"), "description": "Tankstelle", "type": "EXPENSE"},  # new
    ]
    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 1
    assert result.skipped == 1
    assert len(repo.transactions) == 2


@pytest.mark.asyncio
async def test_import_transactions_empty(repo: InMemoryCostRepository) -> None:
    """Empty rows list — both counts are 0."""
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=[], import_source="consorsbank"))

    assert result.imported == 0
    assert result.skipped == 0
```

- [ ] **Step 2: Tests laufen lassen (müssen fehlschlagen)**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_import_transactions_all_new -v
```

Expected: `FAILED` — `cannot import name 'ImportTransactionsUseCase'`

- [ ] **Step 3: Use Case implementieren**

In `backend/src/application/use_cases/cost_use_cases.py`, füge am Ende der Datei hinzu (nach dem letzten Use Case):

```python
@dataclass
class ImportTransactionsInput:
    parsed_rows: list[dict]
    import_source: str


@dataclass
class ImportTransactionsResult:
    imported: int
    skipped: int


class ImportTransactionsUseCase:
    def __init__(self, cost_repo: ICostRepository) -> None:
        self._repo = cost_repo

    async def execute(self, input: ImportTransactionsInput) -> ImportTransactionsResult:
        imported = 0
        skipped = 0
        for row in input.parsed_rows:
            try:
                exists = await self._repo.transaction_exists(
                    row["date"], row["amount"], row["description"]
                )
                if exists:
                    skipped += 1
                else:
                    await self._repo.create_transaction_from_import(row, input.import_source)
                    imported += 1
            except Exception:
                logger.error("Failed to import row: %s", row, exc_info=True)
        return ImportTransactionsResult(imported=imported, skipped=skipped)
```

Stelle sicher dass `logger` und `dataclass` oben importiert sind. Falls nicht:
```python
import logging
from dataclasses import dataclass
logger = logging.getLogger(__name__)
```

- [ ] **Step 4: Tests laufen lassen**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "import_transactions" -v
```

Expected: 4 × PASSED

- [ ] **Step 5: Alle Tests laufen lassen**

```bash
uv run pytest -x -q
```

Expected: Alle Tests grün.

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py \
  backend/tests/application/test_cost_use_cases.py
git commit -m "feat: implement ImportTransactionsUseCase with deduplication"
```

---

## Task 8: `POST /cost/import` Endpoint (TDD)

**Files:**
- Modify: `backend/tests/api/test_cost_router.py`
- Modify: `backend/src/api/routers/cost_router.py`

- [ ] **Step 1: Failing Tests schreiben**

In `backend/tests/api/test_cost_router.py`, füge am Ende an:

```python
# ---------------------------------------------------------------------------
# POST /cost/import
# ---------------------------------------------------------------------------

CONSORSBANK_CSV = b"""Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichw\xc3\xb6rter;Umsatz geteilt;Betrag;W\xc3\xa4hrung
01.05.2026;01.05.2026;John Doe;DE123;BIC123;UEBERWEISUNG;Salary May;n/a;n/a;n/a;5.000,00;EUR
02.05.2026;02.05.2026;Amazon;DE456;BIC456;KARTENZAHLUNG;Laptop;n/a;n/a;n/a;\xe2\x88\x92250,50;EUR
"""

TRADE_REPUBLIC_CSV = b"""Datum,Beschreibung,Typ,Betrag
2026-05-01,Dividend Payment,Income,+50.00
2026-05-02,Stock Purchase,Expense,-1200.00
"""


def test_import_consorsbank_csv(client: TestClient) -> None:
    """POST /cost/import with valid Consorsbank CSV returns 200 with imported count."""
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


def test_import_trade_republic_csv(client: TestClient) -> None:
    """POST /cost/import with valid Trade Republic CSV returns 200 with imported count."""
    resp = client.post(
        "/cost/import",
        files={"file": ("trade_republic_mai2026.csv", TRADE_REPUBLIC_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


def test_import_unknown_filename(client: TestClient) -> None:
    """POST /cost/import with unrecognized filename returns 400."""
    resp = client.post(
        "/cost/import",
        files={"file": ("exports.csv", b"Datum,Betrag\n2026-05-01,100", "text/csv")},
    )
    assert resp.status_code == 400
    assert "consorsbank" in resp.json()["detail"].lower() or "trade_republic" in resp.json()["detail"].lower()


def test_import_malformed_csv(client: TestClient) -> None:
    """POST /cost/import with wrong columns returns 400."""
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_broken.csv", b"WrongCol1;WrongCol2\n1;2", "text/csv")},
    )
    assert resp.status_code == 400


def test_import_duplicate_skipped(client: TestClient) -> None:
    """Second upload of same CSV results in skipped=2, imported=0."""
    client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 0
    assert data["skipped"] == 2
```

- [ ] **Step 2: Tests laufen lassen (müssen fehlschlagen)**

```bash
cd backend && uv run pytest tests/api/test_cost_router.py::test_import_consorsbank_csv -v
```

Expected: `FAILED` — 404 oder `Method Not Allowed`

- [ ] **Step 3: Endpoint implementieren**

In `backend/src/api/routers/cost_router.py`, füge folgende Imports oben hinzu falls nicht vorhanden:

```python
import logging
import tempfile
from pathlib import Path

from fastapi import HTTPException, UploadFile
```

Füge dann am Ende des Routers hinzu:

```python
logger = logging.getLogger(__name__)


@router.post("/import", response_model=dict)
async def import_csv(file: UploadFile, repo: CostRepoDep) -> dict:
    from src.application.use_cases.cost_use_cases import (
        ImportTransactionsInput,
        ImportTransactionsUseCase,
    )
    from src.infrastructure.import_.csv_parser import (
        CSVParser,
        InvalidCSVFormatError,
        InvalidTransactionDataError,
    )

    filename = (file.filename or "").lower()
    if "consorsbank" in filename:
        import_source = "consorsbank"
        parse_fn = CSVParser.parse_consorsbank
    elif "trade_republic" in filename or "traderepublic" in filename:
        import_source = "trade_republic"
        parse_fn = CSVParser.parse_trade_republic
    else:
        raise HTTPException(
            status_code=400,
            detail="Unbekanntes CSV-Format. Dateiname muss 'consorsbank' oder 'trade_republic' enthalten.",
        )

    content = await file.read()
    tmp_path = Path(tempfile.mktemp(suffix=".csv"))
    try:
        tmp_path.write_bytes(content)
        try:
            parsed_rows = parse_fn(tmp_path)
        except (InvalidCSVFormatError, InvalidTransactionDataError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(
        ImportTransactionsInput(parsed_rows=parsed_rows, import_source=import_source)
    )
    return {"imported": result.imported, "skipped": result.skipped}
```

- [ ] **Step 4: Tests laufen lassen**

```bash
cd backend && uv run pytest tests/api/test_cost_router.py -k "import" -v
```

Expected: 5 × PASSED

- [ ] **Step 5: Alle Tests laufen lassen**

```bash
uv run pytest -x -q
```

Expected: Alle Tests grün.

- [ ] **Step 6: Commit**

```bash
git add backend/src/api/routers/cost_router.py \
  backend/tests/api/test_cost_router.py
git commit -m "feat: add POST /cost/import endpoint with deduplication"
```

---

## Task 9: OpenAPI exportieren + TypeScript-Types regenerieren

**Files:**
- Modify: `backend/openapi.json`
- Modify: `frontend/src/api/types.ts`

- [ ] **Step 1: Backend starten und OpenAPI exportieren**

```bash
cd backend && uv run python -m scripts.export_openapi
```

Expected: `backend/openapi.json` aktualisiert (neuer `/cost/import`-Endpoint, kein `/cost/import-status` mehr).

- [ ] **Step 2: TypeScript-Types regenerieren**

```bash
cd frontend && pnpm generate-api-types
```

Expected: `frontend/src/api/types.ts` aktualisiert.

- [ ] **Step 3: TypeScript-Checks laufen lassen**

```bash
pnpm tsc --noEmit
```

Expected: 0 Fehler.

- [ ] **Step 4: Frontend-Tests laufen lassen**

```bash
pnpm test run
```

Expected: Alle Tests grün.

- [ ] **Step 5: Commit**

```bash
git add backend/openapi.json frontend/src/api/types.ts
git commit -m "chore: regenerate OpenAPI spec and TypeScript types"
```

---

## Task 10: Abschluss-Verifikation

- [ ] **Step 1: Alle Backend-Tests laufen lassen**

```bash
cd backend && uv run pytest -q
```

Expected: Alle Tests grün, Anzahl niedriger als vor dem Refactoring (ImportScheduler-Tests entfernt, neue Tests hinzugekommen).

- [ ] **Step 2: Alle Frontend-Tests laufen lassen**

```bash
cd frontend && pnpm test run
```

Expected: Alle Tests grün.

- [ ] **Step 3: PROGRESS.md aktualisieren**

In `PROGRESS.md`:
- Phase 11.5 als ✅ markieren
- Phase 11.1/11.3/11.4 Scheduler-bezogene Items als obsolet markieren
- Neuen Session-Log-Eintrag hinzufügen

- [ ] **Step 4: Commit**

```bash
git add PROGRESS.md
git commit -m "docs: update PROGRESS.md for Phase 11.5 completion"
```
