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
