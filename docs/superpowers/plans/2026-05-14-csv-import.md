# CSV Import Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatisierter wöchentlicher Import von Bank-Transaktionen (CSV) mit Parsing, Scheduling, Archivierung und Status-UI.

**Architecture:** CSVParser parst Consorsbank/Trade Republic CSV-Format → ImportScheduler prüft `/imports` Folder weekly → speichert Transactions in DB → archiviert CSV → Frontend zeigt Status.

**Tech Stack:** APScheduler (Backend-Scheduling), Standard CSV-Library, Pydantic (Validation), TanStack Query (Frontend-Hooks), shadcn/ui (UI-Components).

---

## File Structure

**Backend (new/modified):**
- `src/infrastructure/import/csv_parser.py` — CSVParser Utility (Consorsbank + Trade Republic Parsing)
- `src/application/services/import_scheduler.py` — Weekly Scheduler + Import-Logic
- `src/domain/entities/transaction.py` — Add `import_source` field
- `src/domain/repositories/cost_repository.py` — Add `create_transaction_from_import()` method
- `src/infrastructure/persistence/repositories/cost_repository.py` — Implement `create_transaction_from_import()`
- `src/infrastructure/persistence/mappers.py` — Update Transaction mapper
- `src/config.py` — Add `import_folder` config
- `src/main.py` — Register APScheduler startup
- `src/api/routers/cost_router.py` — Add `GET /cost/import-status` endpoint
- Tests für alle neuen Module

**Frontend (new/modified):**
- `src/features/cost/ImportStatusCard.tsx` — Status-Anzeige-Komponente
- `src/api/hooks/cost.ts` — Add `useImportStatus()` hook
- `src/features/cost/CostManagementPage.tsx` — Integrate ImportStatusCard
- Tests für neue Komponenten + Hooks

**Infrastructure:**
- `docker-compose.yml` — Add `/imports` volume
- `.env.example` — Add `IMPORT_FOLDER`

---

## Tasks

### Task 1: Domain Extension — Transaction.import_source

**Files:**
- Modify: `src/domain/entities/transaction.py`
- Modify: `src/infrastructure/persistence/mappers.py`
- Test: `tests/domain/test_entities.py` (existing)

- [ ] **Step 1: Add import_source field to Transaction entity**

Open `src/domain/entities/transaction.py` and add field:

```python
@dataclass
class Transaction:
    id: UUID
    title: str
    amount: Decimal
    transaction_type: TransactionType
    date: date
    tags: list[str]
    description: str | None = None
    import_source: str | None = None  # NEW: "consorsbank" | "trade_republic" | None
```

- [ ] **Step 2: Run existing domain tests to ensure no breakage**

Run: `cd backend && uv run pytest tests/domain/test_entities.py -v`
Expected: All tests PASS

- [ ] **Step 3: Update Transaction mapper in mappers.py**

Open `src/infrastructure/persistence/mappers.py` and find `transaction_from_model()` function. Add field mapping:

```python
def transaction_from_model(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        title=model.title,
        amount=model.amount,
        transaction_type=TransactionType(model.transaction_type),
        date=model.date,
        tags=model.tags or [],
        description=model.description,
        import_source=model.import_source,  # NEW
    )

def transaction_to_model(transaction: Transaction) -> TransactionModel:
    return TransactionModel(
        id=transaction.id,
        title=transaction.title,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type.value,
        date=transaction.date,
        tags=transaction.tags,
        description=transaction.description,
        import_source=transaction.import_source,  # NEW
    )
```

- [ ] **Step 4: Update SQLAlchemy model**

Open `src/infrastructure/persistence/models.py` and find `TransactionModel`. Add column:

```python
class TransactionModel(Base):
    __tablename__ = "cost_transactions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str]
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    transaction_type: Mapped[str]
    date: Mapped[date]
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    description: Mapped[str | None]
    import_source: Mapped[str | None] = mapped_column(String, nullable=True)  # NEW
    recurring_source_id: Mapped[UUID | None] = mapped_column(ForeignKey(...), nullable=True)
```

- [ ] **Step 5: Create Alembic migration**

Run: `cd backend && alembic revision --autogenerate -m "add transaction import_source field"`

Review generated migration in `alembic/versions/`. Should show:

```python
def upgrade() -> None:
    op.add_column('cost_transactions', sa.Column('import_source', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('cost_transactions', 'import_source')
```

- [ ] **Step 6: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration succeeds

- [ ] **Step 7: Commit**

```bash
cd /Users/nilsworm/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/Task\ Management
git add src/domain/entities/transaction.py src/infrastructure/persistence/mappers.py src/infrastructure/persistence/models.py alembic/versions/*.py
git commit -m "feat: add import_source field to Transaction entity"
```

---

### Task 2: CSVParser Implementation

**Files:**
- Create: `src/infrastructure/import/__init__.py`
- Create: `src/infrastructure/import/csv_parser.py`
- Create: `tests/infrastructure/test_csv_parser.py`

- [ ] **Step 1: Create tests directory structure**

Run: `mkdir -p /Users/nilsworm/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/Task\ Management/backend/tests/infrastructure/import`

- [ ] **Step 2: Write failing tests for Consorsbank parser**

Create `tests/infrastructure/test_csv_parser.py`:

```python
import pytest
from pathlib import Path
from decimal import Decimal
from datetime import date
from src.infrastructure.import.csv_parser import CSVParser, InvalidCSVFormatError, InvalidTransactionDataError


class TestCSVParserConsorsbank:
    
    def test_parse_valid_consorsbank_csv(self):
        """Parse valid Consorsbank CSV with income + expense transactions."""
        csv_content = """Buchungstag,Wertstellung,Umsatzart,Begünstigter / Auftraggeber,Verwendungszweck,Betrag,Saldo
2026-05-01,2026-05-01,UEBERWEISUNG,John Doe,Salary May,+5000.00,10000.00
2026-05-02,2026-05-02,KARTENZAHLUNG,Amazon,Laptop,−250.50,9749.50"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            result = CSVParser.parse_consorsbank(Path(f.name))
        
        assert len(result) == 2
        assert result[0]["date"] == date(2026, 5, 1)
        assert result[0]["amount"] == Decimal("5000.00")
        assert result[0]["type"] == "INCOME"
        assert result[0]["description"] == "John Doe - Salary May"
        
        assert result[1]["date"] == date(2026, 5, 2)
        assert result[1]["amount"] == Decimal("250.50")
        assert result[1]["type"] == "EXPENSE"
        assert result[1]["description"] == "Amazon - Laptop"
    
    def test_parse_consorsbank_missing_columns(self):
        """Raise InvalidCSVFormatError if expected columns are missing."""
        csv_content = "Datum,Betrag\n2026-05-01,1000"
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_consorsbank(Path(f.name))
    
    def test_parse_consorsbank_invalid_amount(self):
        """Raise InvalidTransactionDataError if amount is not parseable."""
        csv_content = """Buchungstag,Wertstellung,Umsatzart,Begünstigter / Auftraggeber,Verwendungszweck,Betrag,Saldo
2026-05-01,2026-05-01,UEBERWEISUNG,John Doe,Salary,INVALID,10000.00"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_consorsbank(Path(f.name))


class TestCSVParserTradeRepublic:
    
    def test_parse_valid_trade_republic_csv(self):
        """Parse valid Trade Republic CSV (pre-converted from PDF)."""
        csv_content = """Datum,Beschreibung,Typ,Betrag
2026-05-01,Dividend Payment,Income,+50.00
2026-05-02,Stock Purchase,Expense,−1200.00"""
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            f.flush()
            
            result = CSVParser.parse_trade_republic(Path(f.name))
        
        assert len(result) == 2
        assert result[0]["date"] == date(2026, 5, 1)
        assert result[0]["amount"] == Decimal("50.00")
        assert result[0]["type"] == "INCOME"
        assert result[0]["description"] == "Dividend Payment"
        
        assert result[1]["date"] == date(2026, 5, 2)
        assert result[1]["amount"] == Decimal("1200.00")
        assert result[1]["type"] == "EXPENSE"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && uv run pytest tests/infrastructure/test_csv_parser.py -v`
Expected: FAIL — "module 'src.infrastructure.import' not found"

- [ ] **Step 4: Create CSVParser module**

Create `src/infrastructure/import/__init__.py` (empty)

Create `src/infrastructure/import/csv_parser.py`:

```python
import csv
from pathlib import Path
from decimal import Decimal
from datetime import datetime


class InvalidCSVFormatError(Exception):
    """Raised when CSV format is invalid (missing expected columns)."""
    pass


class InvalidTransactionDataError(Exception):
    """Raised when individual row data cannot be parsed."""
    pass


class CSVParser:
    
    @staticmethod
    def parse_consorsbank(file_path: Path) -> list[dict]:
        """Parse Consorsbank CSV export.
        
        Expected columns: Buchungstag, Wertstellung, Umsatzart, Begünstigter / Auftraggeber,
                         Verwendungszweck, Betrag, Saldo
        
        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": "INCOME" | "EXPENSE"}]
        """
        required_columns = [
            "Buchungstag", "Wertstellung", "Umsatzart", 
            "Begünstigter / Auftraggeber", "Verwendungszweck", "Betrag", "Saldo"
        ]
        
        result = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate columns
            if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")
            
            for row in reader:
                try:
                    # Parse date
                    date_str = row["Buchungstag"].strip()
                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # Parse amount (handle +/− prefixes)
                    amount_str = row["Betrag"].strip().replace("+", "").replace("−", "-").replace(",", ".")
                    amount = Decimal(amount_str)
                    
                    # Determine type based on sign
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)
                    
                    # Build description
                    description = f"{row['Begünstigter / Auftraggeber'].strip()} - {row['Verwendungszweck'].strip()}"
                    
                    result.append({
                        "date": tx_date,
                        "amount": amount,
                        "type": tx_type,
                        "description": description,
                    })
                except (ValueError, KeyError) as e:
                    raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e
        
        return result
    
    @staticmethod
    def parse_trade_republic(file_path: Path) -> list[dict]:
        """Parse Trade Republic CSV (pre-converted from PDF via kontoauszug.jonathanpagel.com).
        
        Expected columns: Datum, Beschreibung, Typ, Betrag
        
        Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": "INCOME" | "EXPENSE"}]
        """
        required_columns = ["Datum", "Beschreibung", "Typ", "Betrag"]
        
        result = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate columns
            if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
                raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")
            
            for row in reader:
                try:
                    # Parse date
                    date_str = row["Datum"].strip()
                    tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    
                    # Parse amount (handle +/− prefixes)
                    amount_str = row["Betrag"].strip().replace("+", "").replace("−", "-").replace(",", ".")
                    amount = Decimal(amount_str)
                    
                    # Determine type based on sign (override Typ column if needed)
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)
                    
                    description = row["Beschreibung"].strip()
                    
                    result.append({
                        "date": tx_date,
                        "amount": amount,
                        "type": tx_type,
                        "description": description,
                    })
                except (ValueError, KeyError) as e:
                    raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e
        
        return result
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && uv run pytest tests/infrastructure/test_csv_parser.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 6: Commit**

```bash
cd /Users/nilsworm/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/Task\ Management
git add src/infrastructure/import/__init__.py src/infrastructure/import/csv_parser.py tests/infrastructure/test_csv_parser.py
git commit -m "feat: implement CSVParser for Consorsbank and Trade Republic formats"
```

---

### Task 3: Repository Extension — create_transaction_from_import()

**Files:**
- Modify: `src/domain/repositories/cost_repository.py` (interface)
- Modify: `src/infrastructure/persistence/repositories/cost_repository.py` (implementation)
- Test: `tests/infrastructure/test_cost_repository.py` (add integration test)

- [ ] **Step 1: Add interface method to ICostRepository**

Open `src/domain/repositories/cost_repository.py` and add method to `ICostRepository` ABC:

```python
class ICostRepository(ABC):
    # ... existing methods ...
    
    @abstractmethod
    async def create_transaction_from_import(
        self,
        parsed_row: dict,  # {"date": DATE, "amount": DECIMAL, "type": "INCOME"|"EXPENSE", "description": str}
        import_source: str,  # "consorsbank" | "trade_republic"
    ) -> Transaction:
        """Create and persist a Transaction from parsed CSV row.
        
        Sets import_source for audit trail.
        """
        pass
```

- [ ] **Step 2: Implement in PostgresCostRepository**

Open `src/infrastructure/persistence/repositories/cost_repository.py` and add implementation:

```python
async def create_transaction_from_import(
    self,
    parsed_row: dict,
    import_source: str,
) -> Transaction:
    """Create and persist a Transaction from parsed CSV row."""
    
    # Create Transaction entity with parsed data
    transaction = Transaction(
        id=uuid4(),
        title=parsed_row["description"],
        amount=parsed_row["amount"],
        transaction_type=TransactionType(parsed_row["type"]),
        date=parsed_row["date"],
        tags=[],  # No tags on import (Phase 2: intelligent categorization)
        description=None,
        import_source=import_source,
    )
    
    # Persist via existing save_transaction
    await self.save_transaction(transaction)
    
    return transaction
```

- [ ] **Step 3: Write integration test**

Add to `tests/infrastructure/test_cost_repository.py`:

```python
@pytest.mark.asyncio
async def test_create_transaction_from_import_consorsbank():
    """Create transaction from parsed Consorsbank CSV row."""
    parsed_row = {
        "date": date(2026, 5, 1),
        "amount": Decimal("500.00"),
        "type": "EXPENSE",
        "description": "Amazon - Laptop",
    }
    
    repo = PostgresCostRepository(session)
    transaction = await repo.create_transaction_from_import(parsed_row, "consorsbank")
    
    assert transaction.import_source == "consorsbank"
    assert transaction.title == "Amazon - Laptop"
    assert transaction.amount == Decimal("500.00")
    assert transaction.transaction_type == TransactionType.EXPENSE
    
    # Verify persisted in DB
    fetched = await repo.get_transaction(transaction.id)
    assert fetched.import_source == "consorsbank"
```

- [ ] **Step 4: Run integration test**

Run: `cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_create_transaction_from_import_consorsbank -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd /Users/nilsworm/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/Task\ Management
git add src/domain/repositories/cost_repository.py src/infrastructure/persistence/repositories/cost_repository.py tests/infrastructure/test_cost_repository.py
git commit -m "feat: add create_transaction_from_import method to CostRepository"
```

---

### Task 4: Config Extension

**Files:**
- Modify: `src/config.py`
- Modify: `.env.example`

- [ ] **Step 1: Add import_folder to config**

Open `src/config.py` and add field to `Settings`:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    import_folder: str = Field(
        default="/app/imports",
        description="Folder path for CSV import files"
    )
```

- [ ] **Step 2: Update .env.example**

Open `.env.example` and add:

```env
# CSV Import
IMPORT_FOLDER=/app/imports
```

- [ ] **Step 3: Commit**

```bash
cd /Users/nilsworm/Library/Mobile\ Documents/com~apple~CloudDocs/Projects/Task\ Management
git add src/config.py .env.example
git commit -m "config: add IMPORT_FOLDER setting"
```

---

### Task 5: ImportScheduler Implementation

**Files:**
- Create: `src/application/services/import_scheduler.py`
- Test: `tests/application/test_import_scheduler.py`

[Full task text as in plan above]

---

### Task 6: Scheduler Registration in FastAPI

**Files:**
- Modify: `src/main.py`
- Modify: `pyproject.toml` (add apscheduler dependency)

[Full task text as in plan above]

---

### Task 7: Backend API Endpoint — GET /cost/import-status

**Files:**
- Modify: `src/api/routers/cost_router.py`
- Test: `tests/api/test_cost_router.py` (add test)

[Full task text as in plan above]

---

### Task 8: Frontend Hook — useImportStatus

**Files:**
- Modify: `src/api/hooks/cost.ts`
- Test: `tests/api/hooks/cost.test.ts` (add test)

[Full task text as in plan above]

---

### Task 9: Frontend UI — ImportStatusCard Component

**Files:**
- Create: `src/features/cost/ImportStatusCard.tsx`
- Test: `tests/features/cost/ImportStatusCard.test.tsx`

[Full task text as in plan above]

---

### Task 10: Integrate ImportStatusCard into CostManagementPage

**Files:**
- Modify: `src/features/cost/CostManagementPage.tsx`

[Full task text as in plan above]

---

### Task 11: Docker & Environment Setup

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example` (already done in Task 4)

[Full task text as in plan above]

---

### Task 12: Update PROGRESS.md

**Files:**
- Modify: `PROGRESS.md`

[Full task text as in plan above]

---

### Task 13: Final Integration Test — Full Flow

**Files:**
- Create: `tests/e2e/cost_import.spec.ts` (optional, but recommended)

[Full task text as in plan above]
