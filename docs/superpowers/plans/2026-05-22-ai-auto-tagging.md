# AI Auto-Tagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Automatically tag newly imported transactions using the AI client (Ollama or OpenRouter) as a BackgroundTask after each CSV import.

**Architecture:** A new `TagTransactionsUseCase` receives IDs of newly imported transactions, builds a single AI prompt with a fixed `ALLOWED_TAGS` list, parses the JSON response, filters unknown tags, and writes tags back via `ICostRepository.update_tags`. The import endpoint starts this as a FastAPI `BackgroundTask` — the import response is not delayed.

**Tech Stack:** FastAPI BackgroundTasks, SQLAlchemy async UPDATE, existing `IAIClient` abstraction (Ollama / OpenRouter via `AI_PROVIDER` env var)

---

## File Map

| Action | File |
|--------|------|
| Create | `backend/src/domain/cost/tags.py` |
| Create | `backend/src/application/use_cases/tag_transactions.py` |
| Create | `backend/tests/application/test_tag_transactions.py` |
| Modify | `backend/src/domain/cost/repository.py` |
| Modify | `backend/src/infrastructure/persistence/repositories/cost_repository.py` |
| Modify | `backend/src/application/use_cases/cost_use_cases.py` |
| Modify | `backend/src/api/routers/cost_router.py` |
| Modify | `backend/tests/application/test_cost_use_cases.py` |
| Modify | `backend/tests/infrastructure/test_cost_repository.py` |
| Modify | `backend/tests/api/test_cost_router.py` |

---

## Task 1: Tag-Liste

**Files:**
- Create: `backend/src/domain/cost/tags.py`

- [ ] **Step 1: Create the file**

```python
# backend/src/domain/cost/tags.py
from __future__ import annotations

ALLOWED_TAGS: frozenset[str] = frozenset({
    # thematisch
    "lebensmittel", "restaurant", "cafe", "transport", "tanken",
    "wohnen", "nebenkosten", "strom", "internet", "versicherung",
    "gesundheit", "apotheke", "arzt", "kleidung", "elektronik",
    "haushalt", "freizeit", "sport", "reise", "bildung",
    "bücher", "software", "abonnement", "streaming",
    "gehalt", "freelance", "erstattung", "transfer",
    "investition", "sparen", "steuer", "geschenk",
    # bewertend
    "unnötig", "impuls", "ungesund", "tabak", "alkohol",
    "luxury", "wiederkehrend", "einmalig",
})
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/domain/cost/tags.py
git commit -m "feat: add ALLOWED_TAGS constant for AI auto-tagging"
```

---

## Task 2: `ICostRepository.update_tags` Interface + InMemory Stub

**Files:**
- Modify: `backend/src/domain/cost/repository.py`
- Modify: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/application/test_cost_use_cases.py` after the existing tests (before the last line):

```python
@pytest.mark.asyncio
async def test_update_tags_sets_tags_on_transaction(repo: InMemoryCostRepository) -> None:
    tx = await CreateTransactionUseCase(repo).execute(
        CreateTransactionInput(
            title="Rewe",
            amount=Decimal("45.00"),
            transaction_type=TransactionType.EXPENSE,
            date=date(2026, 5, 1),
        )
    )
    await repo.update_tags(tx.id, ["lebensmittel"])
    updated = await repo.get_transaction(tx.id)
    assert updated is not None
    assert updated.tags == ["lebensmittel"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_update_tags_sets_tags_on_transaction -v
```

Expected: FAIL — `InMemoryCostRepository` has no `update_tags` method.

- [ ] **Step 3: Add abstract method to `ICostRepository`**

In `backend/src/domain/cost/repository.py`, add after the `transaction_exists` method (before `reset_all`):

```python
    @abstractmethod
    async def update_tags(self, transaction_id: uuid.UUID, tags: list[str]) -> None:
        """Overwrite the tags on an existing transaction."""
        ...
```

- [ ] **Step 4: Add stub to `InMemoryCostRepository`**

In `backend/tests/application/test_cost_use_cases.py`, add to the `InMemoryCostRepository` class (after `transaction_exists`):

```python
    async def update_tags(self, transaction_id: uuid.UUID, tags: list[str]) -> None:
        tx = self._transactions.get(transaction_id)
        if tx is not None:
            tx.tags = tags
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_update_tags_sets_tags_on_transaction -v
```

Expected: PASS

- [ ] **Step 6: Run full test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all tests pass (no regressions from new abstract method)

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/cost/repository.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: add update_tags to ICostRepository interface and InMemory stub"
```

---

## Task 3: `PostgresCostRepository.update_tags` + Integration Test

**Files:**
- Modify: `backend/src/infrastructure/persistence/repositories/cost_repository.py`
- Modify: `backend/tests/infrastructure/test_cost_repository.py`

- [ ] **Step 1: Write the failing integration test**

Add to `backend/tests/infrastructure/test_cost_repository.py` after the existing tests:

```python
@pytest.mark.asyncio
async def test_update_tags_sets_tags(repo: PostgresCostRepository) -> None:
    tx = _tx(title="Rewe", tags=[])
    await repo.save_transaction(tx)
    await repo.update_tags(tx.id, ["lebensmittel", "unnötig"])
    fetched = await repo.get_transaction(tx.id)
    assert fetched is not None
    assert set(fetched.tags) == {"lebensmittel", "unnötig"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_update_tags_sets_tags -v
```

Expected: FAIL — `PostgresCostRepository` has no `update_tags` method.

- [ ] **Step 3: Add `update` to SQLAlchemy imports**

In `backend/src/infrastructure/persistence/repositories/cost_repository.py`, change the SQLAlchemy import line from:

```python
from sqlalchemy import delete, exists as sa_exists, extract, func, select, union
```

to:

```python
from sqlalchemy import delete, exists as sa_exists, extract, func, select, union, update
```

- [ ] **Step 4: Implement `update_tags` in `PostgresCostRepository`**

Add to `PostgresCostRepository` (after the `transaction_exists` method):

```python
    async def update_tags(self, transaction_id: uuid.UUID, tags: list[str]) -> None:
        await self._session.execute(
            update(TransactionModel)
            .where(TransactionModel.id == transaction_id)
            .values(tags=tags)
        )
        await self._session.commit()
```

- [ ] **Step 5: Run integration test**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_update_tags_sets_tags -v
```

Expected: PASS

- [ ] **Step 6: Run full test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/src/infrastructure/persistence/repositories/cost_repository.py backend/tests/infrastructure/test_cost_repository.py
git commit -m "feat: implement PostgresCostRepository.update_tags"
```

---

## Task 4: `ImportTransactionsResult.new_ids`

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Modify: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write the failing test**

Add to `backend/tests/application/test_cost_use_cases.py`:

```python
@pytest.mark.asyncio
async def test_import_returns_new_ids(repo: InMemoryCostRepository) -> None:
    from src.application.use_cases.cost_use_cases import ImportTransactionsInput, ImportTransactionsUseCase
    rows = [
        {
            "date": date(2026, 5, 1),
            "amount": Decimal("100.00"),
            "type": "INCOME",
            "description": "Gehalt Mai",
        }
    ]
    result = await ImportTransactionsUseCase(repo).execute(
        ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank")
    )
    assert result.imported == 1
    assert len(result.new_ids) == 1
    assert isinstance(result.new_ids[0], uuid.UUID)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_import_returns_new_ids -v
```

Expected: FAIL — `ImportTransactionsResult` has no `new_ids`.

- [ ] **Step 3: Update `ImportTransactionsResult`**

In `backend/src/application/use_cases/cost_use_cases.py`, replace:

```python
@dataclass
class ImportTransactionsResult:
    imported: int
    skipped: int
```

with:

```python
@dataclass
class ImportTransactionsResult:
    imported: int
    skipped: int
    new_ids: list[uuid.UUID] = field(default_factory=list)
```

- [ ] **Step 4: Update `ImportTransactionsUseCase.execute`**

In `backend/src/application/use_cases/cost_use_cases.py`, replace the `execute` method of `ImportTransactionsUseCase`:

```python
    async def execute(self, input: ImportTransactionsInput) -> ImportTransactionsResult:
        imported = 0
        skipped = 0
        new_ids: list[uuid.UUID] = []
        for row in input.parsed_rows:
            try:
                exists = await self._repo.transaction_exists(
                    row["date"], row["amount"], row["description"]
                )
                if exists:
                    skipped += 1
                else:
                    tx = await self._repo.create_transaction_from_import(row, input.import_source)
                    imported += 1
                    new_ids.append(tx.id)
            except Exception:
                logger.error("Failed to import row: %s", row, exc_info=True)
        return ImportTransactionsResult(imported=imported, skipped=skipped, new_ids=new_ids)
```

- [ ] **Step 5: Run test**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_import_returns_new_ids -v
```

Expected: PASS

- [ ] **Step 6: Run full test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: add new_ids to ImportTransactionsResult"
```

---

## Task 5: `TagTransactionsUseCase` + Unit Tests

**Files:**
- Create: `backend/src/application/use_cases/tag_transactions.py`
- Create: `backend/tests/application/test_tag_transactions.py`

- [ ] **Step 1: Create the test file**

Create `backend/tests/application/test_tag_transactions.py`:

```python
from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal
from typing import AsyncIterator

import pytest

from src.application.use_cases.cost_use_cases import CreateTransactionInput, CreateTransactionUseCase
from src.application.use_cases.tag_transactions import TagTransactionsUseCase
from src.domain.ai.client import IAIClient
from src.domain.cost.value_objects import TransactionType
from tests.application.test_cost_use_cases import InMemoryCostRepository


class MockAIClient(IAIClient):
    def __init__(self, response: str) -> None:
        self._response = response

    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system: str) -> str:
        return self._response

    async def generate_stream(
        self, messages: list[dict[str, str]], system: str
    ) -> AsyncIterator[str]:
        yield self._response


class FailingAIClient(IAIClient):
    async def is_available(self) -> bool:
        return False

    async def generate(self, prompt: str, system: str) -> str:
        raise ConnectionError("AI unavailable")

    async def generate_stream(
        self, messages: list[dict[str, str]], system: str
    ) -> AsyncIterator[str]:
        yield ""


@pytest.fixture
def repo() -> InMemoryCostRepository:
    return InMemoryCostRepository()


async def _make_tx(repo: InMemoryCostRepository, title: str) -> uuid.UUID:
    tx = await CreateTransactionUseCase(repo).execute(
        CreateTransactionInput(
            title=title,
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            date=date(2026, 5, 1),
        )
    )
    return tx.id


@pytest.mark.asyncio
async def test_happy_path_sets_tags(repo: InMemoryCostRepository) -> None:
    tid = await _make_tx(repo, "Rewe")
    response = json.dumps([{"id": str(tid), "tags": ["lebensmittel"]}])
    await TagTransactionsUseCase(repo, MockAIClient(response)).execute([tid])
    tx = await repo.get_transaction(tid)
    assert tx is not None
    assert tx.tags == ["lebensmittel"]


@pytest.mark.asyncio
async def test_multiple_tags_per_transaction(repo: InMemoryCostRepository) -> None:
    tid = await _make_tx(repo, "Marlboro")
    response = json.dumps([{"id": str(tid), "tags": ["tabak", "ungesund", "unnötig"]}])
    await TagTransactionsUseCase(repo, MockAIClient(response)).execute([tid])
    tx = await repo.get_transaction(tid)
    assert tx is not None
    assert set(tx.tags) == {"tabak", "ungesund", "unnötig"}


@pytest.mark.asyncio
async def test_unknown_tags_are_filtered(repo: InMemoryCostRepository) -> None:
    tid = await _make_tx(repo, "Rewe")
    response = json.dumps([{"id": str(tid), "tags": ["lebensmittel", "unknown_tag_xyz"]}])
    await TagTransactionsUseCase(repo, MockAIClient(response)).execute([tid])
    tx = await repo.get_transaction(tid)
    assert tx is not None
    assert tx.tags == ["lebensmittel"]


@pytest.mark.asyncio
async def test_invalid_json_does_not_crash(repo: InMemoryCostRepository) -> None:
    tid = await _make_tx(repo, "Rewe")
    await TagTransactionsUseCase(repo, MockAIClient("not valid json {{")).execute([tid])
    tx = await repo.get_transaction(tid)
    assert tx is not None
    assert tx.tags == []


@pytest.mark.asyncio
async def test_ai_error_does_not_crash(repo: InMemoryCostRepository) -> None:
    tid = await _make_tx(repo, "Rewe")
    await TagTransactionsUseCase(repo, FailingAIClient()).execute([tid])
    tx = await repo.get_transaction(tid)
    assert tx is not None
    assert tx.tags == []


@pytest.mark.asyncio
async def test_empty_ids_list_is_noop(repo: InMemoryCostRepository) -> None:
    await TagTransactionsUseCase(repo, MockAIClient("[]")).execute([])
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/application/test_tag_transactions.py -v
```

Expected: FAIL — `TagTransactionsUseCase` not found.

- [ ] **Step 3: Create `TagTransactionsUseCase`**

Create `backend/src/application/use_cases/tag_transactions.py`:

```python
from __future__ import annotations

import json
import logging
import uuid

from src.domain.ai.client import IAIClient
from src.domain.cost.repository import ICostRepository
from src.domain.cost.tags import ALLOWED_TAGS

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Du bist ein Finanz-Kategorisierer. "
    "Antworte ausschließlich mit einem JSON-Array, keine Erklärungen."
)

_PROMPT_TEMPLATE = (
    "Erlaubte Tags: {tags}\n\n"
    "Weise jeder Transaktion passende Tags aus der erlaubten Liste zu. "
    "Mehrere Tags pro Transaktion sind erlaubt. "
    "Transaktionen ohne passenden Tag erhalten ein leeres Array.\n\n"
    "Transaktionen:\n{transactions}\n\n"
    "Antworte ausschließlich mit einem JSON-Array in diesem Format:\n"
    '[{{"id": "<uuid>", "tags": ["tag1", "tag2"]}}, ...]'
)


class TagTransactionsUseCase:
    def __init__(self, cost_repo: ICostRepository, ai_client: IAIClient) -> None:
        self._repo = cost_repo
        self._ai = ai_client

    async def execute(self, transaction_ids: list[uuid.UUID]) -> None:
        if not transaction_ids:
            return

        transactions = []
        for tid in transaction_ids:
            tx = await self._repo.get_transaction(tid)
            if tx is not None:
                transactions.append(tx)

        if not transactions:
            return

        tx_json = json.dumps(
            [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "amount": float(t.amount),
                    "type": t.transaction_type.value,
                    "description": t.description or "",
                }
                for t in transactions
            ],
            ensure_ascii=False,
        )

        prompt = _PROMPT_TEMPLATE.format(
            tags=", ".join(sorted(ALLOWED_TAGS)),
            transactions=tx_json,
        )

        try:
            raw = await self._ai.generate(prompt, _SYSTEM)
        except Exception:
            logger.warning("AI tagging failed: AI unavailable", exc_info=True)
            return

        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results = json.loads(clean)
        except (json.JSONDecodeError, ValueError):
            logger.warning("AI tagging failed: could not parse JSON response")
            return

        for item in results:
            if not isinstance(item, dict):
                continue
            try:
                tid = uuid.UUID(str(item["id"]))
            except (KeyError, ValueError):
                continue
            raw_tags = item.get("tags", [])
            if not isinstance(raw_tags, list):
                continue
            valid_tags = [
                t.strip().lower()
                for t in raw_tags
                if isinstance(t, str) and t.strip().lower() in ALLOWED_TAGS
            ]
            await self._repo.update_tags(tid, valid_tags)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && uv run pytest tests/application/test_tag_transactions.py -v
```

Expected: all 6 tests PASS

- [ ] **Step 5: Run full test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/use_cases/tag_transactions.py backend/tests/application/test_tag_transactions.py
git commit -m "feat: add TagTransactionsUseCase with AI prompt and tag validation"
```

---

## Task 6: BackgroundTask in Import Endpoint + API Test

**Files:**
- Modify: `backend/src/api/routers/cost_router.py`
- Modify: `backend/tests/api/test_cost_router.py`

- [ ] **Step 1: Write the failing API test**

In `backend/tests/api/test_cost_router.py`, add these imports at the top of the file (after the existing imports):

```python
from src.api.dependencies import get_ai_client
from src.domain.ai.client import IAIClient
```

Then add the following fixture and test after the existing import tests (before the Reset section):

```python
class _FixedTagAI(IAIClient):
    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system: str) -> str:
        import re
        ids = re.findall(r'"id":\s*"([0-9a-f-]{36})"', prompt)
        return __import__("json").dumps([{"id": tid, "tags": ["lebensmittel"]} for tid in ids])

    async def generate_stream(self, messages, system):  # type: ignore[override]
        yield ""


@pytest.fixture
def tagging_client(repo: InMemoryCostRepository) -> TestClient:
    app.dependency_overrides[get_cost_repo] = lambda: repo
    app.dependency_overrides[get_ai_client] = lambda: _FixedTagAI()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_import_triggers_auto_tagging(
    tagging_client: TestClient, repo: InMemoryCostRepository
) -> None:
    """After import, background task tags all new transactions via AI."""
    resp = tagging_client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 2
    # BackgroundTask runs synchronously in TestClient
    for tx in repo.transactions:
        assert "lebensmittel" in tx.tags
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/api/test_cost_router.py::test_import_triggers_auto_tagging -v
```

Expected: FAIL — import endpoint doesn't start a BackgroundTask yet.

- [ ] **Step 3: Update imports in `cost_router.py`**

In `backend/src/api/routers/cost_router.py`, change:

```python
from fastapi import APIRouter, HTTPException, Query, UploadFile
```

to:

```python
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, UploadFile
```

And change:

```python
from src.api.dependencies import CostRepoDep
```

to:

```python
from src.api.dependencies import AIClientDep, CostRepoDep
```

- [ ] **Step 4: Update the `import_csv` function signature and body**

In `backend/src/api/routers/cost_router.py`, replace the entire `import_csv` function:

```python
@router.post("/import", response_model=dict)
async def import_csv(
    file: UploadFile,
    repo: CostRepoDep,
    background_tasks: BackgroundTasks,
    ai_client: AIClientDep,
) -> dict:
    from src.application.use_cases.cost_use_cases import (
        ImportTransactionsInput,
        ImportTransactionsUseCase,
    )
    from src.application.use_cases.tag_transactions import TagTransactionsUseCase
    from src.config import settings
    from src.infrastructure.import_.csv_parser import (
        CSVParser,
        InvalidCSVFormatError,
        InvalidTransactionDataError,
    )

    filename = (file.filename or "").lower()
    if "consorsbank" in filename:
        import_source = "consorsbank"

        def parse_fn(path: Path) -> list[dict]:
            return CSVParser.parse_consorsbank(path, own_account_ibans=settings.own_account_ibans)

    elif (
        "trade_republic" in filename
        or "traderepublic" in filename
        or "transaktionsexport" in filename
    ):
        import_source = "trade_republic"

        def parse_fn(path: Path) -> list[dict]:
            return CSVParser.parse_trade_republic(path, own_account_ibans=settings.own_account_ibans)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unbekanntes CSV-Format. Dateiname muss 'consorsbank', 'trade_republic' oder 'transaktionsexport' enthalten.",
        )

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        try:
            parsed_rows = parse_fn(tmp_path)
        except (InvalidCSVFormatError, InvalidTransactionDataError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    result = await ImportTransactionsUseCase(repo).execute(
        ImportTransactionsInput(parsed_rows=parsed_rows, import_source=import_source)
    )

    if result.new_ids:
        background_tasks.add_task(
            TagTransactionsUseCase(repo, ai_client).execute, result.new_ids
        )

    return {"imported": result.imported, "skipped": result.skipped}
```

- [ ] **Step 5: Run the new test**

```bash
cd backend && uv run pytest tests/api/test_cost_router.py::test_import_triggers_auto_tagging -v
```

Expected: PASS

- [ ] **Step 6: Run full test suite**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all tests pass

- [ ] **Step 7: Commit**

```bash
git add backend/src/api/routers/cost_router.py backend/tests/api/test_cost_router.py
git commit -m "feat: trigger AI auto-tagging as background task after CSV import"
```
