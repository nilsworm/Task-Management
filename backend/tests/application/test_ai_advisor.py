from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import AsyncIterator

import pytest

from src.application.services.ai_advisor import AIAdvisorService, InsightCard
from src.domain.cost.entities import Transaction
from src.domain.cost.value_objects import TransactionType
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
    assert "nicht" in cards[0].title.lower() or "nicht" in cards[0].body.lower()


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
    prompt = captured_prompts[0]
    # Income line must show 500€, not conflate with opening balance
    assert "Einnahmen: 500.00€" in prompt
    # Opening balance must be shown separately as Anfangsbestand
    assert "Anfangsbestand" in prompt
    assert "1000.00€" in prompt
    # Account balance (opening + income) correctly shown as 1500€
    assert "Kontostand" in prompt
