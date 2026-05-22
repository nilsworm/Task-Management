# Trade Republic Import + TRANSFER/STOCK Types Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the Trade Republic CSV parser for the real `Transaktionsexport.csv` format, add `TRANSFER` and `STOCK` transaction types, and skip inter-account transfers on the correct side using `OWN_ACCOUNT_IBANS`.

**Architecture:** `TransactionType` gets two new enum values (`TRANSFER`, `STOCK`) stored as strings in the existing `String(10)` column — no DB migration needed. Both parsers receive `own_account_ibans: list[str]` from config to identify own-account transfers. Summary and analytics include TRANSFER/STOCK as separate neutral categories (don't affect balance).

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, pytest, pydantic-settings, TypeScript/React, Recharts

---

## File Map

| File | Change |
|---|---|
| `backend/src/domain/cost/value_objects.py` | Add `TRANSFER`, `STOCK` to `TransactionType` |
| `backend/src/config.py` | Add `own_account_ibans: list[str]` field |
| `.env.example` | Document `OWN_ACCOUNT_IBANS` |
| `backend/src/infrastructure/import_/csv_parser.py` | Rewrite `parse_trade_republic`, update `parse_consorsbank` |
| `backend/src/application/use_cases/cost_use_cases.py` | Update `CostSummary`, `GetCostSummaryUseCase`, `MonthlyComparison`, `GetCostAnalyticsUseCase` |
| `backend/src/api/schemas/cost_schemas.py` | Update `CostSummaryResponse`, `MonthlyComparisonResponse` |
| `backend/src/api/routers/cost_router.py` | Pass `own_account_ibans` to parsers, add `transaktionsexport` detection |
| `backend/openapi.json` | Regenerate |
| `frontend/src/api/types.ts` | Regenerate |
| `frontend/src/features/cost/SummaryCards.tsx` | Show `transfers` + `stock_investments` |
| `frontend/src/features/cost/AnalyticsTab.tsx` | Add transfers + stock to monthly bar chart |
| `backend/tests/infrastructure/import/test_csv_parser.py` | Replace TR tests, add Consorsbank TRANSFER test |
| `backend/tests/application/test_cost_use_cases.py` | Add summary + analytics tests for new types |

---

## Task 1: Add TRANSFER and STOCK to TransactionType

**Files:**
- Modify: `backend/src/domain/cost/value_objects.py`
- Test: `backend/tests/domain/test_cost_value_objects.py` (or nearest existing test file for value objects)

- [ ] **Step 1: Find the existing test file for cost value objects**

```bash
find backend/tests -name "*value*" -o -name "*cost*domain*" | head -5
```

- [ ] **Step 2: Write the failing test**

In whichever test file covers `TransactionType` (check `backend/tests/domain/`), add:

```python
from src.domain.cost.value_objects import TransactionType

def test_transaction_type_has_transfer_and_stock():
    assert TransactionType("transfer") == TransactionType.TRANSFER
    assert TransactionType("stock") == TransactionType.STOCK
    assert TransactionType.TRANSFER.value == "transfer"
    assert TransactionType.STOCK.value == "stock"
```

- [ ] **Step 3: Run to verify it fails**

```bash
cd backend && uv run pytest tests/domain/ -k "test_transaction_type_has_transfer" -v
```

Expected: `FAILED` — `TransactionType has no attribute TRANSFER`

- [ ] **Step 4: Add the two new values**

`backend/src/domain/cost/value_objects.py` currently reads:
```python
class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
```

Change to:
```python
class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"
    TRANSFER = "transfer"
    STOCK = "stock"
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/domain/ -k "test_transaction_type_has_transfer" -v
```

Expected: `PASSED`

- [ ] **Step 6: Run full backend test suite to check for regressions**

```bash
cd backend && uv run pytest tests/ --ignore=tests/infrastructure -x -q
```

Expected: all green (infrastructure tests need a running Postgres — skip them here).

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/cost/value_objects.py backend/tests/
git commit -m "feat: add TRANSFER and STOCK to TransactionType enum"
```

---

## Task 2: Add OWN_ACCOUNT_IBANS to config

**Files:**
- Modify: `backend/src/config.py`
- Modify: `.env.example`

No dedicated test needed — pydantic-settings parsing is framework-level.

- [ ] **Step 1: Add field with validator to `Settings`**

Current `backend/src/config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://..."
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cost_currency: str = "EUR"
    root_path: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    ai_model: str = "meta-llama/llama-3.3-70b-instruct:free"


settings = Settings()
```

Add the new field and validator (add `field_validator` to the pydantic import):

```python
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://..."
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cost_currency: str = "EUR"
    root_path: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
    ai_provider: str = "ollama"
    ai_api_key: str = ""
    ai_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    own_account_ibans: list[str] = []

    @field_validator("own_account_ibans", mode="before")
    @classmethod
    def parse_ibans(cls, v: str | list) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


settings = Settings()
```

- [ ] **Step 2: Document in `.env.example`**

Add after the existing entries:
```
# Comma-separated IBANs of your own bank accounts.
# Used to detect inter-account transfers (TRANSFER type) and skip the receiving side.
# Example: OWN_ACCOUNT_IBANS=DE80760300800270566776,DE44100123450409695601
OWN_ACCOUNT_IBANS=
```

- [ ] **Step 3: Verify the app still starts**

```bash
cd backend && uv run python -c "from src.config import settings; print(settings.own_account_ibans)"
```

Expected: `[]`

- [ ] **Step 4: Commit**

```bash
git add backend/src/config.py .env.example
git commit -m "feat: add OWN_ACCOUNT_IBANS config for own-account IBAN filtering"
```

---

## Task 3: Rewrite parse_trade_republic for real TR CSV format

**Files:**
- Modify: `backend/src/infrastructure/import_/csv_parser.py`
- Modify: `backend/tests/infrastructure/import/test_csv_parser.py`

The real `Transaktionsexport.csv` has columns:
`datetime,date,account_type,category,type,asset_class,name,symbol,shares,price,amount,fee,tax,currency,original_amount,original_currency,fx_rate,description,transaction_id,counterparty_name,counterparty_iban,payment_reference,mcc_code`

- [ ] **Step 1: Replace the three existing TR tests with tests for the real format**

Replace the entire `TestCSVParserTradeRepublic` class in `backend/tests/infrastructure/import/test_csv_parser.py`:

```python
TR_HEADER = '"datetime","date","account_type","category","type","asset_class","name","symbol","shares","price","amount","fee","tax","currency","original_amount","original_currency","fx_rate","description","transaction_id","counterparty_name","counterparty_iban","payment_reference","mcc_code"'

OWN_CONSORSBANK_IBAN = "DE80760300800270566776"


class TestCSVParserTradeRepublic:

    def test_card_expense_interest_dividend_saveback_become_correct_types(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","CASH","CARD_TRANSACTION","","Lidl sagt Danke","","","","-13.120000","","","EUR","","","","TR Card Transaction","id1","","","",""
"2026-05-02T10:00:00Z","2026-05-02","DEFAULT","CASH","INTEREST_PAYMENT","","","","","","0.680000","","-0.18","EUR","","","","Interest payment","id2","","","",""
"2026-05-03T10:00:00Z","2026-05-03","DEFAULT","CASH","DIVIDEND","STOCK","Nike (B)","US6541061031","10.0","","3.300000","","-0.85","EUR","","","","Cash Dividend","id3","","","",""
"2026-05-04T10:00:00Z","2026-05-04","DEFAULT","CASH","BENEFITS_SAVEBACK","FUND","Core MSCI World","IE00B4L5Y983","","","1.250000","","","EUR","","","","Your Saveback","id4","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert len(result) == 4
        assert result[0] == {"date": date(2026, 5, 1), "amount": Decimal("13.120000"), "type": "EXPENSE", "description": "Lidl sagt Danke"}
        assert result[1] == {"date": date(2026, 5, 2), "amount": Decimal("0.680000"), "type": "INCOME", "description": "INTEREST_PAYMENT"}
        assert result[2] == {"date": date(2026, 5, 3), "amount": Decimal("3.300000"), "type": "INCOME", "description": "Nike (B)"}
        assert result[3] == {"date": date(2026, 5, 4), "amount": Decimal("1.250000"), "type": "INCOME", "description": "Core MSCI World"}

    def test_buy_becomes_stock_type(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","TRADING","BUY","FUND","Core MSCI World USD (Acc)","IE00B4L5Y983","1.808168","96.783000","-175.000000","","","EUR","","","","Savings plan execution IE00B4L5Y983","id1","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert len(result) == 1
        assert result[0]["type"] == "STOCK"
        assert result[0]["amount"] == Decimal("175.000000")
        assert result[0]["description"] == "Core MSCI World USD (Acc)"

    def test_transfer_inbound_from_own_iban_is_skipped(self):
        csv_content = f"""{TR_HEADER}
"2026-04-30T02:00:00Z","2026-04-30","DEFAULT","CASH","TRANSFER_INBOUND","","Nils Worm","","","","1500.000000","","","EUR","","","","Incoming transfer from Nils Worm ({OWN_CONSORSBANK_IBAN})","id1","Nils Worm","{OWN_CONSORSBANK_IBAN}","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(
                Path(f.name), own_account_ibans=[OWN_CONSORSBANK_IBAN]
            )

        assert result == []

    def test_free_receipt_and_inpayment_are_skipped(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","DELIVERY","FREE_RECEIPT","FUND","Core MSCI World","IE00B4L5Y983","12.0","","","","","","","","","FREE_RECEIPT","id1","","","",""
"2026-05-02T10:00:00Z","2026-05-02","DEFAULT","CASH","CUSTOMER_INPAYMENT","","","","","","175.000000","","","EUR","","","","Direct Debit Top up with {OWN_CONSORSBANK_IBAN}","id2","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            result = CSVParser.parse_trade_republic(Path(f.name))

        assert result == []

    def test_missing_columns_raises_invalid_format_error(self):
        csv_content = '"date","name"\n"2026-05-01","test"'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            with pytest.raises(InvalidCSVFormatError):
                CSVParser.parse_trade_republic(Path(f.name))

    def test_invalid_amount_raises_invalid_transaction_data_error(self):
        csv_content = f"""{TR_HEADER}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","CASH","CARD_TRANSACTION","","Shop","","","","INVALID","","","EUR","","","","TR Card Transaction","id1","","","",""
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
            f.write(csv_content)
            f.flush()
            with pytest.raises(InvalidTransactionDataError):
                CSVParser.parse_trade_republic(Path(f.name))
```

- [ ] **Step 2: Run the tests to verify they fail**

```bash
cd backend && uv run pytest "tests/infrastructure/import/test_csv_parser.py::TestCSVParserTradeRepublic" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all 6 tests FAILED or ERROR (old parser doesn't match new format).

- [ ] **Step 3: Rewrite `parse_trade_republic` in `backend/src/infrastructure/import_/csv_parser.py`**

First, add `_TR_SKIP_TYPES` as a **class-level attribute** inside the `CSVParser` class (above any method):

```python
class CSVParser:
    _TR_SKIP_TYPES: frozenset[str] = frozenset({"FREE_RECEIPT", "CUSTOMER_INPAYMENT"})
```

Then replace the entire `parse_trade_republic` method with:

```python
_TR_SKIP_TYPES: frozenset[str] = frozenset({"FREE_RECEIPT", "CUSTOMER_INPAYMENT"})

@staticmethod
def parse_trade_republic(
    file_path: Path,
    own_account_ibans: list[str] | None = None,
) -> list[dict]:
    """Parse Trade Republic CSV export (Transaktionsexport.csv).

    Skips FREE_RECEIPT (no cash), CUSTOMER_INPAYMENT (own-account top-up),
    and TRANSFER_INBOUND from own accounts to avoid double-counting.
    BUY transactions become type STOCK (neutral, visible in analytics).

    Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": str}]
    """
    required_columns = ["date", "type", "name", "amount", "counterparty_iban"]
    own_ibans: set[str] = set(own_account_ibans or [])
    result = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not all(col in reader.fieldnames for col in required_columns):
            raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

        for row in reader:
            tx_type_raw = row["type"].strip()

            if tx_type_raw in CSVParser._TR_SKIP_TYPES:
                continue

            if tx_type_raw == "TRANSFER_INBOUND":
                counterparty = row.get("counterparty_iban", "").strip()
                if not own_ibans or counterparty in own_ibans:
                    continue

            try:
                tx_date = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()

                amount_str = row["amount"].strip()
                if not amount_str:
                    continue
                amount = Decimal(amount_str)

                if tx_type_raw == "BUY":
                    tx_type = "STOCK"
                    amount = abs(amount)
                elif amount >= 0:
                    tx_type = "INCOME"
                else:
                    tx_type = "EXPENSE"
                    amount = abs(amount)

                name = row["name"].strip()
                description = name if name else tx_type_raw

                result.append({
                    "date": tx_date,
                    "amount": amount,
                    "type": tx_type,
                    "description": description,
                })
            except (ValueError, KeyError, InvalidOperation) as e:
                raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e

    return result
```

Also remove the old `_TR_SKIP_TYPES` class attribute if it was defined differently before (check and delete if present).

- [ ] **Step 4: Run TR tests to verify they pass**

```bash
cd backend && uv run pytest "tests/infrastructure/import/test_csv_parser.py::TestCSVParserTradeRepublic" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all 6 PASSED.

- [ ] **Step 5: Run full Consorsbank tests to verify no regression**

```bash
cd backend && uv run pytest "tests/infrastructure/import/test_csv_parser.py::TestCSVParserConsorsbank" -v
```

Expected: all 3 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/src/infrastructure/import_/csv_parser.py backend/tests/infrastructure/import/test_csv_parser.py
git commit -m "feat: rewrite parse_trade_republic for real Transaktionsexport.csv format"
```

---

## Task 4: Update parse_consorsbank to emit TRANSFER for own-account rows

**Files:**
- Modify: `backend/src/infrastructure/import_/csv_parser.py`
- Modify: `backend/tests/infrastructure/import/test_csv_parser.py`

- [ ] **Step 1: Add a failing test for the TRANSFER output**

Add to `TestCSVParserConsorsbank` in the test file:

```python
def test_transfer_to_own_account_emits_transfer_type(self):
    """Rows where IBAN matches an own account become TRANSFER type, not EXPENSE."""
    TR_IBAN = "DE44100123450409695601"
    csv_content = f"""Konto
Allgemeine Informationen
Kontostand
Kontoumsätze
Buchung;Valuta;Sender / Empfänger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichwörter;Umsatz geteilt;Betrag;Währung
30.04.2026;30.04.2026;Nils Worm TR;{TR_IBAN};TRBKDEBBXXX;EURO-Überweisung;EURO-Überweisung;n/a;n/a;n/a;-1.500,00;EUR
01.05.2026;01.05.2026;Amazon;DE12345678901234567890;COBADEFFXXX;KARTENZAHLUNG;Laptop;n/a;n/a;n/a;-250,50;EUR"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=True, encoding="utf-8") as f:
        f.write(csv_content)
        f.flush()
        result = CSVParser.parse_consorsbank(Path(f.name), own_account_ibans=[TR_IBAN])

    assert len(result) == 2
    assert result[0]["type"] == "TRANSFER"
    assert result[0]["amount"] == Decimal("1500.00")
    assert result[0]["description"] == "Nils Worm TR"
    assert result[1]["type"] == "EXPENSE"
    assert result[1]["amount"] == Decimal("250.50")
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest "tests/infrastructure/import/test_csv_parser.py::TestCSVParserConsorsbank::test_transfer_to_own_account_emits_transfer_type" -v
```

Expected: FAILED — `parse_consorsbank` doesn't accept `own_account_ibans` yet.

- [ ] **Step 3: Update `parse_consorsbank` to accept and apply `own_account_ibans`**

In `backend/src/infrastructure/import_/csv_parser.py`, change the method signature and add IBAN check:

```python
@staticmethod
def parse_consorsbank(
    file_path: Path,
    own_account_ibans: list[str] | None = None,
) -> list[dict]:
    """Parse Consorsbank CSV export (semicolon-delimited, German format).

    Rows where IBAN matches an entry in own_account_ibans are emitted
    with type TRANSFER instead of INCOME/EXPENSE.

    Returns: [{"date": DATE, "amount": DECIMAL, "description": str, "type": str}]
    """
    required_columns = ["Buchung", "Sender / Empfänger", "Betrag", "Währung"]
    own_ibans: set[str] = set(own_account_ibans or [])
    result = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip() == "Kontoumsätze":
                break

        reader = csv.DictReader(f, delimiter=";")

        if reader.fieldnames is None:
            raise InvalidCSVFormatError("No header row found")

        fieldnames_stripped = [col.strip() if col else col for col in reader.fieldnames]
        if not all(col in fieldnames_stripped for col in required_columns):
            raise InvalidCSVFormatError(f"Missing required columns. Expected: {required_columns}")

        for row in reader:
            try:
                buchung_val = row.get("Buchung ", "") or row.get("Buchung", "")
                if not buchung_val.strip():
                    continue

                tx_date = datetime.strptime(buchung_val.strip(), "%d.%m.%Y").date()

                betrag_val = row.get("Betrag", "").strip()
                amount_str = betrag_val.replace(".", "").replace(",", ".").replace("−", "-")
                amount = Decimal(amount_str)

                description = (row.get("Sender / Empfänger", "") or "").strip()

                iban_val = row.get("IBAN", "").strip()
                if own_ibans and iban_val in own_ibans:
                    tx_type = "TRANSFER"
                    amount = abs(amount)
                else:
                    tx_type = "INCOME" if amount > 0 else "EXPENSE"
                    amount = abs(amount)

                result.append({
                    "date": tx_date,
                    "amount": amount,
                    "type": tx_type,
                    "description": description,
                })
            except (ValueError, KeyError, InvalidOperation) as e:
                raise InvalidTransactionDataError(f"Failed to parse row: {row}") from e

    return result
```

- [ ] **Step 4: Run all CSV parser tests**

```bash
cd backend && uv run pytest "tests/infrastructure/import/test_csv_parser.py" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all 10 tests PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/src/infrastructure/import_/csv_parser.py backend/tests/infrastructure/import/test_csv_parser.py
git commit -m "feat: emit TRANSFER type in consorsbank parser for own-account IBANs"
```

---

## Task 5: Update router to pass own_account_ibans + add transaktionsexport detection

**Files:**
- Modify: `backend/src/api/routers/cost_router.py`
- Test: `backend/tests/api/test_cost_router.py` (find exact path first)

- [ ] **Step 1: Find the cost router test file**

```bash
find backend/tests -name "*cost*" | grep -v __pycache__
```

- [ ] **Step 2: Add a failing test for transaktionsexport filename detection**

In the cost router test file, add (check how existing import tests are structured and mirror the pattern):

```python
async def test_import_transaktionsexport_filename_is_recognized(client: AsyncClient) -> None:
    """Filename 'Transaktionsexport.csv' should be accepted as trade_republic format."""
    # Minimal valid TR CSV
    tr_header = '"datetime","date","account_type","category","type","asset_class","name","symbol","shares","price","amount","fee","tax","currency","original_amount","original_currency","fx_rate","description","transaction_id","counterparty_name","counterparty_iban","payment_reference","mcc_code"'
    csv_content = f"""{tr_header}
"2026-05-01T10:00:00Z","2026-05-01","DEFAULT","CASH","CARD_TRANSACTION","","Lidl","","","","-5.000000","","","EUR","","","","TR Card Transaction","id1","","","",""
"""
    response = await client.post(
        "/cost/import",
        files={"file": ("Transaktionsexport.csv", csv_content.encode(), "text/csv")},
    )
    assert response.status_code == 200
    assert response.json()["imported"] == 1
```

- [ ] **Step 3: Run to verify it fails**

```bash
cd backend && uv run pytest tests/api/ -k "test_import_transaktionsexport" -v
```

Expected: FAILED — 400 "Unbekanntes CSV-Format"

- [ ] **Step 4: Update the router**

In `backend/src/api/routers/cost_router.py`, update the `import_csv` function. Replace the format detection and parser call block:

```python
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
    from src.config import settings

    filename = (file.filename or "").lower()
    if "consorsbank" in filename:
        import_source = "consorsbank"
    elif "trade_republic" in filename or "traderepublic" in filename or "transaktionsexport" in filename:
        import_source = "trade_republic"
    else:
        raise HTTPException(
            status_code=400,
            detail="Unbekanntes CSV-Format. Dateiname muss 'consorsbank', 'trade_republic' oder 'Transaktionsexport' enthalten.",
        )

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        try:
            if import_source == "consorsbank":
                parsed_rows = CSVParser.parse_consorsbank(
                    tmp_path, own_account_ibans=settings.own_account_ibans
                )
            else:
                parsed_rows = CSVParser.parse_trade_republic(
                    tmp_path, own_account_ibans=settings.own_account_ibans
                )
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

- [ ] **Step 5: Run the new test + all API import tests**

```bash
cd backend && uv run pytest tests/api/ -k "import" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all PASSED including the new one.

- [ ] **Step 6: Commit**

```bash
git add backend/src/api/routers/cost_router.py backend/tests/api/
git commit -m "feat: pass own_account_ibans to parsers and detect Transaktionsexport filename"
```

---

## Task 6: Extend CostSummary with transfers + stock_investments

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Modify: `backend/src/api/schemas/cost_schemas.py`
- Test: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write failing tests for the extended summary**

In `backend/tests/application/test_cost_use_cases.py`, add after the existing summary tests:

```python
async def test_summary_includes_transfer_and_stock_totals(repo: InMemoryCostRepository) -> None:
    from datetime import date as dt
    today = date.today()
    # TRANSFER transaction
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="To TR", amount=Decimal("500"),
        transaction_type=TransactionType.TRANSFER,
        date=dt(today.year, today.month, 1),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    # STOCK transaction
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="ETF Buy", amount=Decimal("175"),
        transaction_type=TransactionType.STOCK,
        date=dt(today.year, today.month, 2),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    summary = await GetCostSummaryUseCase(repo).execute(year=today.year, month=today.month)
    assert summary.transfers == Decimal("500")
    assert summary.stock_investments == Decimal("175")
    assert summary.balance == Decimal("0")  # TRANSFER and STOCK don't affect balance

async def test_summary_balance_excludes_transfer_and_stock(repo: InMemoryCostRepository) -> None:
    from datetime import date as dt
    today = date.today()
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="Salary", amount=Decimal("2000"),
        transaction_type=TransactionType.INCOME,
        date=dt(today.year, today.month, 1),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="To TR", amount=Decimal("500"),
        transaction_type=TransactionType.TRANSFER,
        date=dt(today.year, today.month, 2),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    summary = await GetCostSummaryUseCase(repo).execute(year=today.year, month=today.month)
    assert summary.income == Decimal("2000")
    assert summary.balance == Decimal("2000")  # transfer excluded from balance
    assert summary.transfers == Decimal("500")
```

- [ ] **Step 2: Run to verify they fail**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "transfer_and_stock" -v
```

Expected: FAILED — `CostSummary has no attribute transfers`

- [ ] **Step 3: Extend `CostSummary` dataclass and `GetCostSummaryUseCase`**

In `backend/src/application/use_cases/cost_use_cases.py`, update the `CostSummary` dataclass (currently around line 30):

```python
@dataclass
class CostSummary:
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    balance: Decimal
    transfers: Decimal
    stock_investments: Decimal
```

Update `GetCostSummaryUseCase.execute` (currently around line 232):

```python
async def execute(self, year: int, month: int) -> CostSummary:
    transactions = await self._repo.list_transactions(year=year, month=month)
    income = sum(
        (t.amount for t in transactions if t.transaction_type == TransactionType.INCOME),
        Decimal("0"),
    )
    expenses = sum(
        (t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE),
        Decimal("0"),
    )
    transfers = sum(
        (t.amount for t in transactions if t.transaction_type == TransactionType.TRANSFER),
        Decimal("0"),
    )
    stock_investments = sum(
        (t.amount for t in transactions if t.transaction_type == TransactionType.STOCK),
        Decimal("0"),
    )
    return CostSummary(
        year=year,
        month=month,
        income=income,
        expenses=expenses,
        balance=income - expenses,
        transfers=transfers,
        stock_investments=stock_investments,
    )
```

- [ ] **Step 4: Update `CostSummaryResponse` in `backend/src/api/schemas/cost_schemas.py`**

The `CostSummaryResponse` class currently:
```python
class CostSummaryResponse(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    balance: Decimal
```

Change to:
```python
class CostSummaryResponse(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    balance: Decimal
    transfers: Decimal
    stock_investments: Decimal
```

- [ ] **Step 5: Update the router that builds `CostSummaryResponse`**

In `backend/src/api/routers/cost_router.py`, find the `get_cost_summary` endpoint. It currently returns:
```python
return CostSummaryResponse(
    year=summary.year,
    month=summary.month,
    income=summary.income,
    expenses=summary.expenses,
    balance=summary.balance,
)
```

Change to:
```python
return CostSummaryResponse(
    year=summary.year,
    month=summary.month,
    income=summary.income,
    expenses=summary.expenses,
    balance=summary.balance,
    transfers=summary.transfers,
    stock_investments=summary.stock_investments,
)
```

- [ ] **Step 6: Run all summary tests**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "summary" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all PASSED.

- [ ] **Step 7: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/src/api/schemas/cost_schemas.py backend/src/api/routers/cost_router.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: add transfers and stock_investments to CostSummary"
```

---

## Task 7: Extend MonthlyComparison with transfers + stock

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Modify: `backend/src/api/schemas/cost_schemas.py`
- Test: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write a failing test for analytics monthly comparison**

Add to `backend/tests/application/test_cost_use_cases.py`:

```python
async def test_analytics_monthly_comparison_includes_transfers_and_stock(repo: InMemoryCostRepository) -> None:
    from datetime import date as dt
    today = date.today()
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="To TR", amount=Decimal("500"),
        transaction_type=TransactionType.TRANSFER,
        date=dt(today.year, today.month, 1),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    await repo.save_transaction(Transaction(
        id=uuid.uuid4(), title="ETF", amount=Decimal("175"),
        transaction_type=TransactionType.STOCK,
        date=dt(today.year, today.month, 2),
        tags=[], description=None, recurring_source_id=None,
        import_source=None, is_opening_balance=False,
    ))
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=today.year, month=today.month)
    current = next(m for m in analytics.monthly_comparison if m.year == today.year and m.month == today.month)
    assert current.transfers == Decimal("500")
    assert current.stock_investments == Decimal("175")
```

- [ ] **Step 2: Run to verify it fails**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "analytics_monthly_comparison_includes" -v
```

Expected: FAILED — `MonthlyComparison has no attribute transfers`

- [ ] **Step 3: Extend `MonthlyComparison` dataclass**

In `backend/src/application/use_cases/cost_use_cases.py`, update `MonthlyComparison` (currently around line 270):

```python
@dataclass
class MonthlyComparison:
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    transfers: Decimal
    stock_investments: Decimal
```

- [ ] **Step 4: Update `GetCostAnalyticsUseCase` to populate the new fields**

In the same file, update the comparison loop (currently around line 305):

```python
comparison: list[MonthlyComparison] = []
for y, m in _last_n_months(year, month, n=6):
    txs = await self._repo.list_transactions(year=y, month=m, tags=tags)
    income = sum(
        (t.amount for t in txs if t.transaction_type == TransactionType.INCOME),
        Decimal("0"),
    )
    exps = sum(
        (t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE),
        Decimal("0"),
    )
    transfers = sum(
        (t.amount for t in txs if t.transaction_type == TransactionType.TRANSFER),
        Decimal("0"),
    )
    stock_investments = sum(
        (t.amount for t in txs if t.transaction_type == TransactionType.STOCK),
        Decimal("0"),
    )
    comparison.append(MonthlyComparison(
        year=y, month=m,
        income=income, expenses=exps,
        transfers=transfers, stock_investments=stock_investments,
    ))
```

- [ ] **Step 5: Update `MonthlyComparisonResponse` and `CostAnalyticsResponse.from_domain` in schemas**

In `backend/src/api/schemas/cost_schemas.py`, find `MonthlyComparisonResponse` and add the new fields:

```python
class MonthlyComparisonResponse(BaseModel):
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    transfers: Decimal
    stock_investments: Decimal
```

Update the `from_domain` factory in `CostAnalyticsResponse` to pass the new fields:

```python
MonthlyComparisonResponse(
    year=mc.year,
    month=mc.month,
    income=mc.income,
    expenses=mc.expenses,
    transfers=mc.transfers,
    stock_investments=mc.stock_investments,
)
```

- [ ] **Step 6: Run all analytics tests**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -k "analytic" -v 2>&1 | grep -E "PASSED|FAILED|ERROR"
```

Expected: all PASSED.

- [ ] **Step 7: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/src/api/schemas/cost_schemas.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: add transfers and stock_investments to MonthlyComparison analytics"
```

---

## Task 8: Regenerate OpenAPI + update frontend

**Files:**
- Modify: `backend/openapi.json`
- Modify: `frontend/src/api/types.ts`
- Modify: `frontend/src/features/cost/SummaryCards.tsx`
- Modify: `frontend/src/features/cost/AnalyticsTab.tsx`

- [ ] **Step 1: Regenerate OpenAPI spec**

```bash
cd backend && uv run python -c "
import json
from src.main import app
import asyncio

async def export():
    from httpx import AsyncClient, ASGITransport
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        r = await client.get('/openapi.json')
        with open('openapi.json', 'w') as f:
            json.dump(r.json(), f, indent=2)
        print('Done')

asyncio.run(export())
"
```

- [ ] **Step 2: Regenerate TypeScript types**

```bash
cd frontend && pnpm generate-api-types
```

- [ ] **Step 3: Update `SummaryCards.tsx` to show TRANSFER and STOCK cards**

Find `frontend/src/features/cost/SummaryCards.tsx`. It currently renders 3 cards (income, expenses, balance). Add two more cards after the balance card:

```tsx
// After the existing balance card, add:
<div className="rounded-lg border border-border bg-surface-2 p-4">
  <p className="text-xs text-secondary uppercase tracking-wide">Transfers</p>
  <p className="mt-1 text-xl font-mono font-semibold text-cyan-400">
    {formatAmount(summary.transfers)} {currency}
  </p>
</div>
<div className="rounded-lg border border-border bg-surface-2 p-4">
  <p className="text-xs text-secondary uppercase tracking-wide">Investments</p>
  <p className="mt-1 text-xl font-mono font-semibold text-purple-400">
    {formatAmount(summary.stock_investments)} {currency}
  </p>
</div>
```

Note: check the exact prop name for `summary` in this component and mirror the styling of the existing cards exactly.

- [ ] **Step 4: Update `AnalyticsTab.tsx` to add transfers + stock bars to the monthly bar chart**

Find the `BarChart` in `frontend/src/features/cost/AnalyticsTab.tsx` that renders `monthly_comparison`. It currently has bars for `income` and `expenses`. Add two more `Bar` elements:

```tsx
<Bar dataKey="transfers" name="Transfers" fill="var(--color-cyan)" opacity={0.7} />
<Bar dataKey="stock_investments" name="Investments" fill="var(--color-purple)" opacity={0.7} />
```

- [ ] **Step 5: TypeScript check**

```bash
cd frontend && pnpm tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 6: Run frontend tests**

```bash
cd frontend && pnpm test run
```

Expected: all green.

- [ ] **Step 7: Run full backend test suite (excluding infrastructure which needs Postgres)**

```bash
cd backend && uv run pytest tests/ --ignore=tests/infrastructure -q
```

Expected: all green.

- [ ] **Step 8: Commit**

```bash
git add backend/openapi.json frontend/src/api/types.ts frontend/src/features/cost/SummaryCards.tsx frontend/src/features/cost/AnalyticsTab.tsx
git commit -m "feat: update frontend to display transfers and stock_investments"
```
