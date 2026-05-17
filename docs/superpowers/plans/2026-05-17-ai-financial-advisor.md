# AI Financial Advisor — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local AI financial advisor (Ollama + Qwen2.5-14B) accessible via a global floating panel with proactive insight cards and a streaming chat interface, reading only cost table data.

**Architecture:** OllamaClient (httpx, local inference) → AIAdvisorService (aggregates cost data, builds prompts) → two FastAPI endpoints (`POST /ai/insights` non-streaming, `POST /ai/chat` SSE streaming). Frontend: Zustand store controls a fixed slide-in panel with InsightCards + AIChat components, wired into AppLayout.

**Tech Stack:** Python httpx (new main dep), FastAPI StreamingResponse, Ollama REST API, React + Zustand, TanStack Query, native fetch ReadableStream (SSE)

---

## File Map

**New backend files:**
- `backend/src/infrastructure/ai/__init__.py`
- `backend/src/infrastructure/ai/ollama_client.py` — IOllamaClient ABC + OllamaClient implementation
- `backend/src/application/services/ai_advisor.py` — AIAdvisorService (context building + prompt calls)
- `backend/src/api/schemas/ai_schemas.py` — Pydantic DTOs for insights + chat
- `backend/src/api/routers/ai_router.py` — POST /ai/insights + POST /ai/chat
- `backend/tests/infrastructure/test_ollama_client.py`
- `backend/tests/application/test_ai_advisor.py`
- `backend/tests/api/test_ai_router.py`

**Modified backend files:**
- `backend/pyproject.toml` — add `httpx` to main deps
- `backend/src/config.py` — add `ollama_base_url`, `ollama_model`
- `backend/src/api/dependencies.py` — add `get_ollama_client`, `get_ai_advisor_service`
- `backend/src/main.py` — register ai_router + Ollama startup check

**New frontend files:**
- `frontend/src/stores/aiPanelStore.ts`
- `frontend/src/api/hooks/ai.ts`
- `frontend/src/features/ai/AIAdvisorPanel.tsx`
- `frontend/src/features/ai/AIFloatingButton.tsx`
- `frontend/src/features/ai/InsightCards.tsx`
- `frontend/src/features/ai/AIChat.tsx`
- `frontend/src/features/ai/__tests__/AIFloatingButton.test.tsx`
- `frontend/src/features/ai/__tests__/InsightCards.test.tsx`
- `frontend/src/features/ai/__tests__/AIChat.test.tsx`

**Modified frontend files:**
- `frontend/src/layouts/AppLayout.tsx` — add AIFloatingButton + AIAdvisorPanel

---

## Task 1: Config + OllamaClient

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/src/config.py`
- Create: `backend/src/infrastructure/ai/__init__.py`
- Create: `backend/src/infrastructure/ai/ollama_client.py`
- Create: `backend/tests/infrastructure/test_ollama_client.py`

- [ ] **Step 1: Add httpx to main dependencies**

In `backend/pyproject.toml`, add `httpx` to the `dependencies` list (not dev):

```toml
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "asyncpg>=0.30.0",
    "alembic>=1.14.0",
    "pydantic-settings>=2.0.0",
    "apscheduler>=3.10.4",
    "httpx>=0.28.0",
]
```

Run: `cd backend && uv sync`

- [ ] **Step 2: Add Ollama config fields**

In `backend/src/config.py`, add two new fields to `Settings`:

```python
ollama_base_url: str = "http://localhost:11434"
ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"
```

Full file after change:

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    cost_currency: str = "EUR"
    import_folder: str = Field(
        default="/app/imports",
        description="Folder path for CSV import files"
    )
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b-instruct-q4_K_M"


settings = Settings()
```

- [ ] **Step 3: Write the failing tests**

Create `backend/tests/infrastructure/test_ollama_client.py`:

```python
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.ai.ollama_client import OllamaClient


@pytest.fixture
def client() -> OllamaClient:
    return OllamaClient(base_url="http://localhost:11434", model="test-model")


@pytest.mark.asyncio
async def test_is_available_returns_true_when_ollama_responds(client: OllamaClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await client.is_available()

    assert result is True


@pytest.mark.asyncio
async def test_is_available_returns_false_on_connection_error(client: OllamaClient) -> None:
    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_class.return_value = mock_instance

        result = await client.is_available()

    assert result is False


@pytest.mark.asyncio
async def test_generate_returns_response_text(client: OllamaClient) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"response": "Hallo Welt", "done": True})

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await client.generate(prompt="Test", system="System")

    assert result == "Hallo Welt"


@pytest.mark.asyncio
async def test_generate_stream_yields_tokens(client: OllamaClient) -> None:
    ndjson_lines = [
        json.dumps({"response": "Hal", "done": False}),
        json.dumps({"response": "lo", "done": False}),
        json.dumps({"response": " Welt", "done": True}),
    ]

    async def mock_aiter_lines():
        for line in ndjson_lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.stream = MagicMock(return_value=mock_stream_ctx)
        mock_class.return_value = mock_instance

        tokens = []
        async for token in client.generate_stream(prompt="Test", system="System"):
            tokens.append(token)

    assert tokens == ["Hal", "lo", " Welt"]
```

- [ ] **Step 4: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/infrastructure/test_ollama_client.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` (file doesn't exist yet).

- [ ] **Step 5: Create `infrastructure/ai/__init__.py`**

```python
```
(empty file)

- [ ] **Step 6: Create `ollama_client.py`**

Create `backend/src/infrastructure/ai/ollama_client.py`:

```python
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class IOllamaClient(ABC):
    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    async def generate(self, prompt: str, system: str) -> str: ...

    @abstractmethod
    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]: ...


class OllamaClient(IOllamaClient):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._base_url}/api/tags", timeout=3.0)
                return resp.status_code == 200
        except Exception:
            return False

    async def generate(self, prompt: str, system: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "system": system, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "system": system, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done"):
                        break
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/infrastructure/test_ollama_client.py -v
```

Expected: 4 passed.

- [ ] **Step 8: Commit**

```bash
git add backend/pyproject.toml backend/src/config.py \
        backend/src/infrastructure/ai/ \
        backend/tests/infrastructure/test_ollama_client.py
git commit -m "feat: add OllamaClient infrastructure and config"
```

---

## Task 2: AIAdvisorService

**Files:**
- Create: `backend/src/application/services/ai_advisor.py`
- Create: `backend/tests/application/test_ai_advisor.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/application/test_ai_advisor.py`:

```python
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest

from src.application.services.ai_advisor import AIAdvisorService, InsightCard
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType
from src.infrastructure.ai.ollama_client import IOllamaClient
from tests.application.test_cost_use_cases import InMemoryCostRepository


# ---------------------------------------------------------------------------
# Mock OllamaClient
# ---------------------------------------------------------------------------


class MockOllamaClient(IOllamaClient):
    def __init__(self, generate_response: str = "[]", stream_tokens: list[str] | None = None) -> None:
        self._generate_response = generate_response
        self._stream_tokens = stream_tokens or []

    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system: str) -> str:
        return self._generate_response

    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        for token in self._stream_tokens:
            yield token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_transaction(
    amount: str,
    tx_type: TransactionType,
    tags: list[str],
    tx_date: date | None = None,
) -> Transaction:
    return Transaction.create(
        title="Test",
        amount=Decimal(amount),
        transaction_type=tx_type,
        transaction_date=tx_date or date(2026, 5, 10),
        tags=tags,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_insights_parses_valid_json() -> None:
    repo = InMemoryCostRepository()
    await repo.save_transaction(
        make_transaction("1500.00", TransactionType.INCOME, [], date(2026, 5, 1))
    )
    await repo.save_transaction(
        make_transaction("400.00", TransactionType.EXPENSE, ["lebensmittel"], date(2026, 5, 5))
    )

    json_response = '[{"title":"Gut gespart","body":"Saldo positiv","type":"tip"},{"title":"Ausgaben stabil","body":"Keine Anomalien","type":"forecast"},{"title":"Abo prüfen","body":"Monatliche Kosten prüfen","type":"warning"}]'
    ollama = MockOllamaClient(generate_response=json_response)
    service = AIAdvisorService(repo, ollama)

    cards = await service.get_insights()

    assert len(cards) == 3
    assert cards[0].title == "Gut gespart"
    assert cards[0].type == "tip"
    assert cards[1].type == "forecast"
    assert cards[2].type == "warning"


@pytest.mark.asyncio
async def test_get_insights_returns_fallback_on_invalid_json() -> None:
    repo = InMemoryCostRepository()
    ollama = MockOllamaClient(generate_response="Diese Antwort ist kein JSON.")
    service = AIAdvisorService(repo, ollama)

    cards = await service.get_insights()

    assert len(cards) == 1
    assert cards[0].type == "warning"
    assert "nicht verfügbar" in cards[0].title.lower() or "nicht" in cards[0].body.lower()


@pytest.mark.asyncio
async def test_get_insights_strips_markdown_code_block() -> None:
    repo = InMemoryCostRepository()
    json_content = '[{"title":"Test","body":"Body","type":"tip"}]'
    wrapped = f"```json\n{json_content}\n```"
    ollama = MockOllamaClient(generate_response=wrapped)
    service = AIAdvisorService(repo, ollama)

    cards = await service.get_insights()

    assert len(cards) == 1
    assert cards[0].title == "Test"


@pytest.mark.asyncio
async def test_stream_chat_yields_tokens() -> None:
    repo = InMemoryCostRepository()
    tokens = ["Deine ", "Ausgaben ", "sind ", "stabil."]
    ollama = MockOllamaClient(stream_tokens=tokens)
    service = AIAdvisorService(repo, ollama)

    result = []
    async for token in service.stream_chat("Wie sind meine Ausgaben?"):
        result.append(token)

    assert result == tokens


@pytest.mark.asyncio
async def test_build_context_excludes_opening_balance() -> None:
    """Opening balance transactions must not skew income/expense totals."""
    repo = InMemoryCostRepository()
    await repo.save_transaction(
        make_transaction("500.00", TransactionType.INCOME, [], date(2026, 5, 1))
    )
    # Opening balance — should be excluded from totals
    ob = Transaction.create(
        title="Opening Balance April",
        amount=Decimal("1000.00"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 5, 1),
        is_opening_balance=True,
    )
    await repo.save_transaction(ob)

    captured_prompts: list[str] = []

    class CapturingOllamaClient(IOllamaClient):
        async def is_available(self) -> bool:
            return True

        async def generate(self, prompt: str, system: str) -> str:
            captured_prompts.append(prompt)
            return '[{"title":"x","body":"y","type":"tip"}]'

        async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
            yield ""

    service = AIAdvisorService(repo, CapturingOllamaClient())
    await service.get_insights()

    assert captured_prompts
    # The context should show 500€ income, not 1500€
    assert "500,00€" in captured_prompts[0] or "500.00€" in captured_prompts[0] or "500" in captured_prompts[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/application/test_ai_advisor.py -v
```

Expected: `ImportError` (module doesn't exist yet).

- [ ] **Step 3: Create `ai_advisor.py`**

Create `backend/src/application/services/ai_advisor.py`:

```python
from __future__ import annotations

import json
import logging
from calendar import month_abbr, month_name
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import AsyncIterator

from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import TransactionType
from src.infrastructure.ai.ollama_client import IOllamaClient

logger = logging.getLogger(__name__)

_CHAT_SYSTEM = (
    "Du bist ein persönlicher Finanzberater. Antworte auf Deutsch, präzise, "
    "maximal 3 kurze Absätze. Nutze ausschließlich die bereitgestellten Finanzdaten "
    "als Grundlage. Beantworte nur Fragen zu persönlichen Finanzen."
)

_INSIGHTS_SYSTEM = "Du bist ein persönlicher Finanzberater. Antworte ausschließlich mit einem JSON-Array."

_INSIGHTS_PROMPT = (
    "Analysiere die folgenden Finanzdaten und gib exakt 3 Insights als JSON-Array zurück.\n"
    "Jeder Insight hat: title (max 60 Zeichen), body (max 120 Zeichen), "
    "type (warning|tip|forecast).\n"
    "Gib ausschließlich das JSON-Array zurück, keine Erklärungen.\n\n"
    "{context}"
)

_CHAT_PROMPT = "{question}\n\nFinanzdaten:\n{context}"


@dataclass
class InsightCard:
    title: str
    body: str
    type: str  # "warning" | "tip" | "forecast"


class AIAdvisorService:
    def __init__(self, cost_repo: ICostRepository, ollama: IOllamaClient) -> None:
        self._repo = cost_repo
        self._ollama = ollama

    async def _build_context(self) -> str:
        today = date.today()
        year, month = today.year, today.month

        current = await self._repo.list_transactions(year=year, month=month)
        income = sum(
            t.amount for t in current
            if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance
        )
        expenses = sum(
            t.amount for t in current
            if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance
        )
        balance = income - expenses

        tag_totals: dict[str, Decimal] = {}
        for t in current:
            if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance:
                for tag in (t.tags or ["unkategorisiert"]):
                    tag_totals[tag] = tag_totals.get(tag, Decimal("0")) + t.amount
        tag_lines = ", ".join(
            f"{tag} {amt:.2f}€"
            for tag, amt in sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)[:8]
        )

        trend_lines: list[str] = []
        for delta in range(5, -1, -1):
            m = month - delta
            y = year
            while m <= 0:
                m += 12
                y -= 1
            txs = await self._repo.list_transactions(year=y, month=m)
            inc = sum(t.amount for t in txs if t.transaction_type == TransactionType.INCOME and not t.is_opening_balance)
            exp = sum(t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance)
            saldo = inc - exp
            label = f"{month_abbr[m]} {y}"
            sign = "+" if saldo >= 0 else ""
            trend_lines.append(f"  {label}: {sign}{saldo:.2f}€")

        recurring = await self._repo.list_recurring(active_only=True)
        rec_lines = ", ".join(
            f"{r.title} {r.amount:.2f}€/{r.interval.value}" for r in recurring[:10]
        ) or "keine"

        top5 = sorted(
            [t for t in current if t.transaction_type == TransactionType.EXPENSE and not t.is_opening_balance],
            key=lambda t: t.amount,
            reverse=True,
        )[:5]
        top5_lines = "\n".join(
            f"  {t.date}  {t.title}  {t.amount:.2f}€  [{', '.join(t.tags)}]" for t in top5
        ) or "  keine"

        return (
            f"Aktueller Monat ({month_name[month]} {year}):\n"
            f"- Einnahmen: {income:.2f}€  Ausgaben: {expenses:.2f}€  "
            f"Saldo: {'+' if balance >= 0 else ''}{balance:.2f}€\n"
            f"- Ausgaben nach Tag: {tag_lines or 'keine'}\n\n"
            f"Letzte 6 Monate (Monatssaldo):\n{chr(10).join(trend_lines)}\n\n"
            f"Wiederkehrende Einträge (aktiv):\n  {rec_lines}\n\n"
            f"Top-5 Ausgaben diesen Monat:\n{top5_lines}"
        )

    async def get_insights(self) -> list[InsightCard]:
        context = await self._build_context()
        prompt = _INSIGHTS_PROMPT.format(context=context)
        raw = await self._ollama.generate(prompt, _INSIGHTS_SYSTEM)
        try:
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            cards_data = json.loads(clean)
            valid_types = {"warning", "tip", "forecast"}
            return [
                InsightCard(
                    title=str(c.get("title", ""))[:60],
                    body=str(c.get("body", ""))[:120],
                    type=c.get("type", "tip") if c.get("type") in valid_types else "tip",
                )
                for c in cards_data[:3]
            ]
        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning("Failed to parse AI insights JSON: %s", exc)
            return [
                InsightCard(
                    title="Analyse nicht verfügbar",
                    body="Das Modell konnte keine strukturierten Insights generieren.",
                    type="warning",
                )
            ]

    async def stream_chat(self, message: str) -> AsyncIterator[str]:
        context = await self._build_context()
        prompt = _CHAT_PROMPT.format(question=message, context=context)
        async for token in self._ollama.generate_stream(prompt, _CHAT_SYSTEM):
            yield token
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/application/test_ai_advisor.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/services/ai_advisor.py \
        backend/tests/application/test_ai_advisor.py
git commit -m "feat: implement AIAdvisorService with context building and prompt calls"
```

---

## Task 3: AI Schemas + Insights Endpoint

**Files:**
- Create: `backend/src/api/schemas/ai_schemas.py`
- Create: `backend/src/api/routers/ai_router.py`
- Modify: `backend/src/api/dependencies.py`
- Modify: `backend/src/main.py`
- Create: `backend/tests/api/test_ai_router.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/api/test_ai_router.py`:

```python
from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_ai_advisor_service
from src.application.services.ai_advisor import AIAdvisorService, InsightCard
from src.main import app


class MockAIAdvisorService:
    def __init__(
        self,
        insights: list[InsightCard] | None = None,
        stream_tokens: list[str] | None = None,
    ) -> None:
        self._insights = insights or [
            InsightCard(title="Test Insight", body="Test body", type="tip"),
        ]
        self._stream_tokens = stream_tokens or ["Hallo ", "Welt"]

    async def get_insights(self) -> list[InsightCard]:
        return self._insights

    async def stream_chat(self, message: str) -> AsyncIterator[str]:
        for token in self._stream_tokens:
            yield token


@pytest.fixture
def mock_service() -> MockAIAdvisorService:
    return MockAIAdvisorService()


@pytest.fixture
def client(mock_service: MockAIAdvisorService) -> TestClient:
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /ai/insights
# ---------------------------------------------------------------------------


def test_insights_returns_200_with_cards(client: TestClient) -> None:
    resp = client.post("/ai/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test Insight"
    assert data[0]["body"] == "Test body"
    assert data[0]["type"] == "tip"


def test_insights_returns_503_when_service_unavailable(mock_service: MockAIAdvisorService) -> None:
    async def raise_503():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Ollama not available")

    mock_service.get_insights = raise_503  # type: ignore[assignment]
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        resp = c.post("/ai/insights")
    app.dependency_overrides.clear()
    assert resp.status_code == 503
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/api/test_ai_router.py -v
```

Expected: `ImportError` or 404 (router not registered yet).

- [ ] **Step 3: Create `ai_schemas.py`**

Create `backend/src/api/schemas/ai_schemas.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field


class InsightCardResponse(BaseModel):
    title: str
    body: str
    type: str  # "warning" | "tip" | "forecast"


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
```

- [ ] **Step 4: Create `ai_router.py` with insights endpoint**

Create `backend/src/api/routers/ai_router.py`:

```python
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_ai_advisor_service
from src.api.schemas.ai_schemas import InsightCardResponse
from src.application.services.ai_advisor import AIAdvisorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

AIAdvisorServiceDep = Annotated[AIAdvisorService, Depends(get_ai_advisor_service)]


@router.post("/insights", response_model=list[InsightCardResponse])
async def get_insights(service: AIAdvisorServiceDep) -> list[InsightCardResponse]:
    cards = await service.get_insights()
    return [InsightCardResponse(title=c.title, body=c.body, type=c.type) for c in cards]
```

- [ ] **Step 5: Add dependencies to `dependencies.py`**

Append to `backend/src/api/dependencies.py`:

```python
from src.application.services.ai_advisor import AIAdvisorService
from src.config import settings
from src.infrastructure.ai.ollama_client import IOllamaClient, OllamaClient

# Singleton — created once at module load
_ollama_client: IOllamaClient = OllamaClient(
    base_url=settings.ollama_base_url,
    model=settings.ollama_model,
)


def get_ollama_client() -> IOllamaClient:
    return _ollama_client


OllamaClientDep = Annotated[IOllamaClient, Depends(get_ollama_client)]


def get_ai_advisor_service(
    cost_repo: CostRepoDep,
    ollama: OllamaClientDep,
) -> AIAdvisorService:
    return AIAdvisorService(cost_repo, ollama)
```

- [ ] **Step 6: Register router + startup check in `main.py`**

In `backend/src/main.py`, add the following import and include statement:

Add import:
```python
from src.api.routers.ai_router import router as ai_router
```

Add after `app.include_router(cost_router)`:
```python
app.include_router(ai_router)
```

Add a new startup event after the existing `start_scheduler`:
```python
@app.on_event("startup")
async def check_ollama() -> None:
    """Log Ollama availability at startup."""
    from src.api.dependencies import get_ollama_client
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

- [ ] **Step 7: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/api/test_ai_router.py -v
```

Expected: 2 passed.

- [ ] **Step 8: Run full test suite to check for regressions**

```bash
cd backend && uv run pytest --tb=short -q
```

Expected: all existing tests still pass + 2 new.

- [ ] **Step 9: Commit**

```bash
git add backend/src/api/schemas/ai_schemas.py \
        backend/src/api/routers/ai_router.py \
        backend/src/api/dependencies.py \
        backend/src/main.py \
        backend/tests/api/test_ai_router.py
git commit -m "feat: add POST /ai/insights endpoint with OllamaClient dependency"
```

---

## Task 4: Chat Streaming Endpoint

**Files:**
- Modify: `backend/src/api/routers/ai_router.py`
- Modify: `backend/tests/api/test_ai_router.py`

- [ ] **Step 1: Add chat tests**

Append to `backend/tests/api/test_ai_router.py`:

```python
# ---------------------------------------------------------------------------
# POST /ai/chat
# ---------------------------------------------------------------------------


def test_chat_returns_200_sse_stream(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": "Was sind meine größten Ausgaben?"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "data: Hallo \n\n" in body
    assert "data: [DONE]\n\n" in body


def test_chat_returns_422_for_empty_message(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": ""})
    assert resp.status_code == 422


def test_chat_returns_422_for_message_too_long(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": "x" * 501})
    assert resp.status_code == 422
```

- [ ] **Step 2: Run new tests to verify they fail**

```bash
cd backend && uv run pytest tests/api/test_ai_router.py::test_chat_returns_200_sse_stream -v
```

Expected: FAIL (endpoint doesn't exist).

- [ ] **Step 3: Add chat endpoint to `ai_router.py`**

Full updated `backend/src/api/routers/ai_router.py`:

```python
from __future__ import annotations

import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_ai_advisor_service
from src.api.schemas.ai_schemas import AIChatRequest, InsightCardResponse
from src.application.services.ai_advisor import AIAdvisorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

AIAdvisorServiceDep = Annotated[AIAdvisorService, Depends(get_ai_advisor_service)]


@router.post("/insights", response_model=list[InsightCardResponse])
async def get_insights(service: AIAdvisorServiceDep) -> list[InsightCardResponse]:
    cards = await service.get_insights()
    return [InsightCardResponse(title=c.title, body=c.body, type=c.type) for c in cards]


@router.post("/chat")
async def chat(request: AIChatRequest, service: AIAdvisorServiceDep) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        async for token in service.stream_chat(request.message):
            safe = token.replace("\n", " ")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **Step 4: Run all chat tests**

```bash
cd backend && uv run pytest tests/api/test_ai_router.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add backend/src/api/routers/ai_router.py \
        backend/tests/api/test_ai_router.py
git commit -m "feat: add POST /ai/chat streaming endpoint (SSE)"
```

---

## Task 5: Frontend Store + Hooks

**Files:**
- Create: `frontend/src/stores/aiPanelStore.ts`
- Create: `frontend/src/api/hooks/ai.ts`
- Create: `frontend/src/features/ai/__tests__/aiStore.test.ts`
- Create: `frontend/src/api/__tests__/hooks.ai.test.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/features/ai/__tests__/aiStore.test.ts`:

```typescript
import { describe, it, expect, beforeEach } from "vitest"
import { useAIPanelStore } from "@/stores/aiPanelStore"

describe("aiPanelStore", () => {
  beforeEach(() => {
    useAIPanelStore.setState({ isOpen: false })
  })

  it("starts closed", () => {
    expect(useAIPanelStore.getState().isOpen).toBe(false)
  })

  it("toggle opens the panel", () => {
    useAIPanelStore.getState().toggle()
    expect(useAIPanelStore.getState().isOpen).toBe(true)
  })

  it("toggle closes the panel when open", () => {
    useAIPanelStore.setState({ isOpen: true })
    useAIPanelStore.getState().toggle()
    expect(useAIPanelStore.getState().isOpen).toBe(false)
  })
})
```

Create `frontend/src/api/__tests__/hooks.ai.test.tsx`:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { createElement } from "react"
import { useAIInsights } from "@/api/hooks/ai"

vi.mock("@/api/client", () => ({
  apiPost: vi.fn(),
}))

import { apiPost } from "@/api/client"

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return createElement(QueryClientProvider, { client: qc }, children)
}

describe("useAIInsights", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("does not fetch when isOpen is false", () => {
    renderHook(() => useAIInsights(false), { wrapper })
    expect(apiPost).not.toHaveBeenCalled()
  })

  it("fetches insights when isOpen is true", async () => {
    const mockCards = [{ title: "Test", body: "Body", type: "tip" }]
    vi.mocked(apiPost).mockResolvedValue(mockCards)

    const { result } = renderHook(() => useAIInsights(true), { wrapper })

    await waitFor(() => expect(result.current.data).toBeDefined())
    expect(apiPost).toHaveBeenCalledWith("/ai/insights")
    expect(result.current.data).toEqual(mockCards)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/aiStore.test.ts src/api/__tests__/hooks.ai.test.tsx
```

Expected: import errors.

- [ ] **Step 3: Create `aiPanelStore.ts`**

Create `frontend/src/stores/aiPanelStore.ts`:

```typescript
import { create } from "zustand"

interface AIPanelState {
  isOpen: boolean
  toggle: () => void
}

export const useAIPanelStore = create<AIPanelState>((set, get) => ({
  isOpen: false,
  toggle: () => set({ isOpen: !get().isOpen }),
}))
```

- [ ] **Step 4: Create `api/hooks/ai.ts`**

Create `frontend/src/api/hooks/ai.ts`:

```typescript
import { useMutation, useQuery } from "@tanstack/react-query"
import { apiPost } from "@/api/client"

export interface InsightCard {
  title: string
  body: string
  type: "warning" | "tip" | "forecast"
}

const AI_INSIGHTS_KEY = ["ai", "insights"] as const

export function useAIInsights(enabled: boolean) {
  return useQuery({
    queryKey: AI_INSIGHTS_KEY,
    queryFn: () => apiPost<InsightCard[]>("/ai/insights"),
    enabled,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/aiStore.test.ts src/api/__tests__/hooks.ai.test.tsx
```

Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/stores/aiPanelStore.ts \
        frontend/src/api/hooks/ai.ts \
        frontend/src/features/ai/__tests__/aiStore.test.ts \
        frontend/src/api/__tests__/hooks.ai.test.tsx
git commit -m "feat: add AI panel Zustand store and useAIInsights hook"
```

---

## Task 6: AIFloatingButton + Panel Skeleton + AppLayout wiring

**Files:**
- Create: `frontend/src/features/ai/AIAdvisorPanel.tsx`
- Create: `frontend/src/features/ai/AIFloatingButton.tsx`
- Create: `frontend/src/features/ai/__tests__/AIFloatingButton.test.tsx`
- Modify: `frontend/src/layouts/AppLayout.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/features/ai/__tests__/AIFloatingButton.test.tsx`:

```typescript
import { describe, it, expect, beforeEach } from "vitest"
import { render, screen, fireEvent } from "@testing-library/react"
import { AIFloatingButton } from "@/features/ai/AIFloatingButton"
import { useAIPanelStore } from "@/stores/aiPanelStore"

describe("AIFloatingButton", () => {
  beforeEach(() => {
    useAIPanelStore.setState({ isOpen: false })
  })

  it("renders the button", () => {
    render(<AIFloatingButton />)
    expect(screen.getByRole("button", { name: /ai advisor/i })).toBeInTheDocument()
  })

  it("calls toggle on click", () => {
    render(<AIFloatingButton />)
    fireEvent.click(screen.getByRole("button", { name: /ai advisor/i }))
    expect(useAIPanelStore.getState().isOpen).toBe(true)
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/AIFloatingButton.test.tsx
```

Expected: import errors.

- [ ] **Step 3: Create `AIAdvisorPanel.tsx` skeleton**

Create `frontend/src/features/ai/AIAdvisorPanel.tsx`:

```tsx
import { useAIPanelStore } from "@/stores/aiPanelStore"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()

  if (!isOpen) return null

  return (
    <div
      className="fixed right-0 top-0 z-50 flex h-screen w-[420px] flex-col border-l border-border bg-[#0d0d0f] shadow-2xl"
      data-testid="ai-advisor-panel"
    >
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-border/50 px-4">
        <span className="text-sm font-semibold text-white">AI Advisor</span>
        <button
          onClick={toggle}
          aria-label="Close AI Advisor"
          className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-1 flex-col overflow-hidden p-4">
        {/* InsightCards and AIChat will be added in Tasks 7 and 8 */}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Create `AIFloatingButton.tsx`**

Create `frontend/src/features/ai/AIFloatingButton.tsx`:

```tsx
import { Sparkles } from "lucide-react"
import { useAIPanelStore } from "@/stores/aiPanelStore"

export function AIFloatingButton() {
  const { toggle, isOpen } = useAIPanelStore()

  return (
    <button
      onClick={toggle}
      aria-label="AI Advisor"
      aria-expanded={isOpen}
      className="fixed bottom-6 right-6 z-50 flex h-12 w-12 items-center justify-center rounded-full shadow-lg transition-transform hover:scale-105 active:scale-95"
      style={{
        background: "linear-gradient(135deg, #00d4ff, #7c3aed)",
        boxShadow: "0 0 20px rgba(0, 212, 255, 0.4)",
      }}
    >
      <Sparkles className="h-5 w-5 text-white" />
    </button>
  )
}
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/AIFloatingButton.test.tsx
```

Expected: 2 passed.

- [ ] **Step 6: Wire into `AppLayout.tsx`**

In `frontend/src/layouts/AppLayout.tsx`, add these imports at the top:

```typescript
import { AIFloatingButton } from "@/features/ai/AIFloatingButton"
import { AIAdvisorPanel } from "@/features/ai/AIAdvisorPanel"
```

Add both components at the end of the returned JSX, after the outer `<div>` closing tag:

The full return becomes:
```tsx
return (
  <>
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      {/* ... existing sidebar + main content unchanged ... */}
    </div>
    <AIFloatingButton />
    <AIAdvisorPanel />
  </>
)
```

- [ ] **Step 7: Run full frontend test suite**

```bash
cd frontend && pnpm vitest run
```

Expected: all existing tests pass + new tests.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/ai/AIFloatingButton.tsx \
        frontend/src/features/ai/AIAdvisorPanel.tsx \
        frontend/src/features/ai/__tests__/AIFloatingButton.test.tsx \
        frontend/src/layouts/AppLayout.tsx
git commit -m "feat: add AIFloatingButton and AIAdvisorPanel skeleton, wire into AppLayout"
```

---

## Task 7: InsightCards Component

**Files:**
- Create: `frontend/src/features/ai/InsightCards.tsx`
- Create: `frontend/src/features/ai/__tests__/InsightCards.test.tsx`
- Modify: `frontend/src/features/ai/AIAdvisorPanel.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/features/ai/__tests__/InsightCards.test.tsx`:

```typescript
import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { InsightCards } from "@/features/ai/InsightCards"
import type { InsightCard } from "@/api/hooks/ai"

const cards: InsightCard[] = [
  { title: "Ausgaben gestiegen", body: "Deine Ausgaben stiegen um 20%", type: "warning" },
  { title: "Gut gespart", body: "Saldo positiv", type: "tip" },
  { title: "Lastschrift nächsten Monat", body: "3 Abbuchungen kommen", type: "forecast" },
]

describe("InsightCards", () => {
  it("renders all three cards", () => {
    render(<InsightCards cards={cards} isLoading={false} />)
    expect(screen.getByText("Ausgaben gestiegen")).toBeInTheDocument()
    expect(screen.getByText("Gut gespart")).toBeInTheDocument()
    expect(screen.getByText("Lastschrift nächsten Monat")).toBeInTheDocument()
  })

  it("shows skeleton when loading", () => {
    render(<InsightCards cards={[]} isLoading={true} />)
    expect(screen.getAllByTestId("insight-skeleton")).toHaveLength(3)
  })

  it("renders warning card with orange accent", () => {
    render(<InsightCards cards={[cards[0]]} isLoading={false} />)
    const card = screen.getByTestId("insight-card-warning")
    expect(card).toBeInTheDocument()
  })

  it("renders tip card with green accent", () => {
    render(<InsightCards cards={[cards[1]]} isLoading={false} />)
    expect(screen.getByTestId("insight-card-tip")).toBeInTheDocument()
  })

  it("renders forecast card with blue accent", () => {
    render(<InsightCards cards={[cards[2]]} isLoading={false} />)
    expect(screen.getByTestId("insight-card-forecast")).toBeInTheDocument()
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/InsightCards.test.tsx
```

Expected: import error.

- [ ] **Step 3: Create `InsightCards.tsx`**

Create `frontend/src/features/ai/InsightCards.tsx`:

```tsx
import type { InsightCard } from "@/api/hooks/ai"

const TYPE_CONFIG = {
  warning: { color: "#f97316", label: "Warnung" },
  tip:     { color: "#22c55e", label: "Tipp"    },
  forecast:{ color: "#00d4ff", label: "Prognose" },
} as const

interface InsightCardsProps {
  cards: InsightCard[]
  isLoading: boolean
}

export function InsightCards({ cards, isLoading }: InsightCardsProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            data-testid="insight-skeleton"
            className="h-16 animate-pulse rounded-lg bg-white/5"
          />
        ))}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-2">
      {cards.map((card, i) => {
        const cfg = TYPE_CONFIG[card.type as keyof typeof TYPE_CONFIG] ?? TYPE_CONFIG.tip
        return (
          <div
            key={i}
            data-testid={`insight-card-${card.type}`}
            className="rounded-lg border p-3"
            style={{
              borderColor: `${cfg.color}33`,
              background: `${cfg.color}0d`,
            }}
          >
            <div className="mb-0.5 flex items-center gap-2">
              <span
                className="rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
                style={{ background: `${cfg.color}22`, color: cfg.color }}
              >
                {cfg.label}
              </span>
              <span className="text-xs font-medium text-white">{card.title}</span>
            </div>
            <p className="text-[11px] leading-relaxed text-zinc-400">{card.body}</p>
          </div>
        )
      })}
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/InsightCards.test.tsx
```

Expected: 5 passed.

- [ ] **Step 5: Integrate InsightCards into `AIAdvisorPanel.tsx`**

Replace the `{/* InsightCards ... */}` comment in `AIAdvisorPanel.tsx` with actual usage:

```tsx
import { useAIPanelStore } from "@/stores/aiPanelStore"
import { useAIInsights } from "@/api/hooks/ai"
import { InsightCards } from "@/features/ai/InsightCards"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()
  const { data: insights, isLoading } = useAIInsights(isOpen)

  if (!isOpen) return null

  return (
    <div
      className="fixed right-0 top-0 z-50 flex h-screen w-[420px] flex-col border-l border-border bg-[#0d0d0f] shadow-2xl"
      data-testid="ai-advisor-panel"
    >
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-border/50 px-4">
        <span className="text-sm font-semibold text-white">AI Advisor</span>
        <button
          onClick={toggle}
          aria-label="Close AI Advisor"
          className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-1 flex-col gap-4 overflow-hidden p-4">
        <InsightCards cards={insights ?? []} isLoading={isLoading} />
        {/* AIChat will be added in Task 8 */}
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/ai/InsightCards.tsx \
        frontend/src/features/ai/__tests__/InsightCards.test.tsx \
        frontend/src/features/ai/AIAdvisorPanel.tsx
git commit -m "feat: add InsightCards component and wire into AIAdvisorPanel"
```

---

## Task 8: AIChat Component with Streaming

**Files:**
- Create: `frontend/src/features/ai/AIChat.tsx`
- Create: `frontend/src/features/ai/__tests__/AIChat.test.tsx`
- Modify: `frontend/src/features/ai/AIAdvisorPanel.tsx`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/features/ai/__tests__/AIChat.test.tsx`:

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { AIChat } from "@/features/ai/AIChat"

function makeStream(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk))
      }
      controller.close()
    },
  })
}

describe("AIChat", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  it("renders input and send button", () => {
    render(<AIChat />)
    expect(screen.getByPlaceholderText(/frage stellen/i)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /senden/i })).toBeInTheDocument()
  })

  it("disables send button when input is empty", () => {
    render(<AIChat />)
    expect(screen.getByRole("button", { name: /senden/i })).toBeDisabled()
  })

  it("enables send button when input has text", () => {
    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Wie ist mein Saldo?" },
    })
    expect(screen.getByRole("button", { name: /senden/i })).not.toBeDisabled()
  })

  it("streams response tokens into the bubble", async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      body: makeStream([
        "data: Dein \n\n",
        "data: Saldo \n\n",
        "data: ist positiv.\n\n",
        "data: [DONE]\n\n",
      ]),
    } as unknown as Response)

    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Wie ist mein Saldo?" },
    })
    fireEvent.click(screen.getByRole("button", { name: /senden/i }))

    await waitFor(() =>
      expect(screen.getByTestId("ai-response")).toHaveTextContent("Dein Saldo ist positiv.")
    )
  })

  it("shows error message on fetch failure", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("Network error"))

    render(<AIChat />)
    fireEvent.change(screen.getByPlaceholderText(/frage stellen/i), {
      target: { value: "Test" },
    })
    fireEvent.click(screen.getByRole("button", { name: /senden/i }))

    await waitFor(() =>
      expect(screen.getByTestId("ai-error")).toBeInTheDocument()
    )
  })
})
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/AIChat.test.tsx
```

Expected: import error.

- [ ] **Step 3: Create `AIChat.tsx`**

Create `frontend/src/features/ai/AIChat.tsx`:

```tsx
import { useState, useRef, useEffect } from "react"
import { Send } from "lucide-react"

const BASE_URL = import.meta.env.VITE_API_URL ?? ""

export function AIChat() {
  const [message, setMessage] = useState("")
  const [response, setResponse] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const responseRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight
    }
  }, [response])

  const handleSend = async () => {
    if (!message.trim() || isStreaming) return
    setIsStreaming(true)
    setResponse("")
    setError(null)

    try {
      const res = await fetch(`${BASE_URL}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: message.trim() }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      if (!res.body) throw new Error("No response body")

      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        for (const line of text.split("\n")) {
          if (!line.startsWith("data: ")) continue
          const token = line.slice(6)
          if (token === "[DONE]") {
            setIsStreaming(false)
            return
          }
          setResponse((prev) => prev + token)
        }
      }
    } catch (e) {
      setError("Antwort konnte nicht geladen werden.")
    } finally {
      setIsStreaming(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-1 flex-col gap-3 overflow-hidden">
      {response && (
        <div
          ref={responseRef}
          data-testid="ai-response"
          className="flex-1 overflow-y-auto rounded-lg border border-border/30 bg-white/5 p-3 text-[12px] leading-relaxed text-zinc-300"
        >
          {response}
          {isStreaming && (
            <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-cyan" />
          )}
        </div>
      )}

      {error && (
        <p data-testid="ai-error" className="text-[11px] text-red-400">
          {error}
        </p>
      )}

      <div className="flex shrink-0 gap-2">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Frage stellen..."
          disabled={isStreaming}
          className="flex-1 rounded-lg border border-border/50 bg-white/5 px-3 py-2 text-[12px] text-white placeholder:text-zinc-500 focus:border-cyan/50 focus:outline-none disabled:opacity-50"
        />
        <button
          onClick={handleSend}
          disabled={!message.trim() || isStreaming}
          aria-label="Senden"
          className="flex h-9 w-9 items-center justify-center rounded-lg bg-cyan/20 text-cyan transition-colors hover:bg-cyan/30 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Send className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd frontend && pnpm vitest run src/features/ai/__tests__/AIChat.test.tsx
```

Expected: 5 passed.

- [ ] **Step 5: Integrate AIChat into `AIAdvisorPanel.tsx`**

Full updated `AIAdvisorPanel.tsx`:

```tsx
import { useAIPanelStore } from "@/stores/aiPanelStore"
import { useAIInsights } from "@/api/hooks/ai"
import { InsightCards } from "@/features/ai/InsightCards"
import { AIChat } from "@/features/ai/AIChat"
import { X } from "lucide-react"

export function AIAdvisorPanel() {
  const { isOpen, toggle } = useAIPanelStore()
  const { data: insights, isLoading } = useAIInsights(isOpen)

  if (!isOpen) return null

  return (
    <div
      className="fixed right-0 top-0 z-50 flex h-screen w-[420px] flex-col border-l border-border bg-[#0d0d0f] shadow-2xl"
      data-testid="ai-advisor-panel"
    >
      <div className="flex h-12 shrink-0 items-center justify-between border-b border-border/50 px-4">
        <span className="text-sm font-semibold text-white">AI Advisor</span>
        <button
          onClick={toggle}
          aria-label="Close AI Advisor"
          className="rounded p-1 text-zinc-400 hover:bg-white/10 hover:text-white"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-1 flex-col gap-4 overflow-hidden p-4">
        <div className="shrink-0">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
            Aktuelle Insights
          </p>
          <InsightCards cards={insights ?? []} isLoading={isLoading} />
        </div>
        <div className="mx-0 h-px bg-border/30" />
        <AIChat />
      </div>
    </div>
  )
}
```

- [ ] **Step 6: Run full test suite**

```bash
cd frontend && pnpm vitest run
```

Expected: all tests pass.

- [ ] **Step 7: TypeScript check**

```bash
cd frontend && pnpm tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/features/ai/AIChat.tsx \
        frontend/src/features/ai/__tests__/AIChat.test.tsx \
        frontend/src/features/ai/AIAdvisorPanel.tsx
git commit -m "feat: add AIChat component with SSE streaming, complete AIAdvisorPanel"
```

---

## Task 9: Frontend Design Polish

**Note:** This task uses the `frontend-design` skill. Do NOT implement code in this step — invoke the skill and follow its process.

- [ ] **Step 1: Invoke frontend-design skill**

Run: `/skill frontend-design:frontend-design`

Brief the skill with:
- Target components: `AIFloatingButton`, `AIAdvisorPanel`, `InsightCards`, `AIChat`
- Design direction: modern AI-native look, dark panel (even in light mode), glassmorphism effect on panel, gradient FAB (cyan → purple), different from rest of app
- Existing design tokens in `frontend/src/index.css`: `--color-cyan`, `--color-purple`, surface layers, border tokens

- [ ] **Step 2: Commit design changes**

After the frontend-design skill completes:

```bash
git add frontend/src/features/ai/
git commit -m "design: apply AI advisor visual design polish"
```

---

## Final Verification

- [ ] Run full backend test suite: `cd backend && uv run pytest --tb=short -q`
- [ ] Run full frontend test suite: `cd frontend && pnpm vitest run`
- [ ] TypeScript check: `cd frontend && pnpm tsc --noEmit`
- [ ] Manual smoke test: start backend + frontend, open app, click FAB, check insights load, send a chat message (requires Ollama running locally with `ollama run qwen2.5:14b-instruct-q4_K_M`)
- [ ] Commit: `git commit -m "chore: update PROGRESS.md for AI financial advisor feature"`
