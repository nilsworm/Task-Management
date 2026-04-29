from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.application.use_cases.cost_use_cases import (
    CreateRecurringInput,
    CreateRecurringUseCase,
    CreateTransactionInput,
    CreateTransactionUseCase,
    DeleteRecurringUseCase,
    DeleteTransactionUseCase,
    ListCostTagsUseCase,
    ListRecurringUseCase,
    ListTransactionsUseCase,
)
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


# ---------------------------------------------------------------------------
# InMemory stub
# ---------------------------------------------------------------------------


class InMemoryCostRepository(ICostRepository):
    def __init__(self) -> None:
        self._transactions: dict[uuid.UUID, Transaction] = {}
        self._recurring: dict[uuid.UUID, RecurringTransaction] = {}

    async def save_transaction(self, transaction: Transaction) -> None:
        self._transactions[transaction.id] = transaction

    async def get_transaction(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self._transactions.get(transaction_id)

    async def list_transactions(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]:
        result = list(self._transactions.values())
        if year is not None:
            result = [t for t in result if t.date.year == year]
        if month is not None:
            result = [t for t in result if t.date.month == month]
        if transaction_type is not None:
            result = [t for t in result if t.transaction_type == transaction_type]
        if tags:
            result = [t for t in result if any(tag in t.tags for tag in tags)]
        return sorted(result, key=lambda t: t.date, reverse=True)

    async def delete_transaction(self, transaction_id: uuid.UUID) -> None:
        self._transactions.pop(transaction_id, None)

    async def save_recurring(self, recurring: RecurringTransaction) -> None:
        self._recurring[recurring.id] = recurring

    async def get_recurring(self, recurring_id: uuid.UUID) -> RecurringTransaction | None:
        return self._recurring.get(recurring_id)

    async def list_recurring(self, active_only: bool = False) -> list[RecurringTransaction]:
        result = list(self._recurring.values())
        if active_only:
            result = [r for r in result if r.is_active]
        return result

    async def delete_recurring(self, recurring_id: uuid.UUID) -> None:
        self._recurring.pop(recurring_id, None)

    async def list_all_tags(self) -> list[str]:
        tags: set[str] = set()
        for t in self._transactions.values():
            tags.update(t.tags)
        for r in self._recurring.values():
            tags.update(r.tags)
        return sorted(tags)


@pytest.fixture
def repo() -> InMemoryCostRepository:
    return InMemoryCostRepository()


def _expense_input(
    title: str = "Miete",
    amount: str = "800.00",
    tx_date: date | None = None,
    tags: list[str] | None = None,
) -> CreateTransactionInput:
    return CreateTransactionInput(
        title=title,
        amount=Decimal(amount),
        transaction_type=TransactionType.EXPENSE,
        date=tx_date or date.today(),
        tags=tags or [],
    )


def _income_input(title: str = "Gehalt", amount: str = "3000.00") -> CreateTransactionInput:
    return CreateTransactionInput(
        title=title,
        amount=Decimal(amount),
        transaction_type=TransactionType.INCOME,
        date=date.today(),
    )


# ---------------------------------------------------------------------------
# CreateTransaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_transaction_stores_entity(repo: InMemoryCostRepository) -> None:
    uc = CreateTransactionUseCase(repo)
    t = await uc.execute(_expense_input())
    assert repo._transactions[t.id].title == "Miete"


@pytest.mark.asyncio
async def test_create_transaction_returns_entity(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(_income_input())
    assert t.transaction_type is TransactionType.INCOME
    assert t.amount == Decimal("3000.00")


# ---------------------------------------------------------------------------
# ListTransactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_transactions_empty(repo: InMemoryCostRepository) -> None:
    result = await ListTransactionsUseCase(repo).execute()
    assert result == []


@pytest.mark.asyncio
async def test_list_transactions_filter_by_month(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(tx_date=date(2026, 4, 1)))
    await create.execute(_expense_input(tx_date=date(2026, 3, 1)))

    result = await ListTransactionsUseCase(repo).execute(year=2026, month=4)
    assert len(result) == 1
    assert result[0].date == date(2026, 4, 1)


@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input())
    await create.execute(_income_input())

    expenses = await ListTransactionsUseCase(repo).execute(
        transaction_type=TransactionType.EXPENSE
    )
    assert all(t.transaction_type is TransactionType.EXPENSE for t in expenses)
    assert len(expenses) == 1


@pytest.mark.asyncio
async def test_list_transactions_filter_by_tag(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(tags=["miete"]))
    await create.execute(_expense_input(tags=["lebensmittel"]))

    result = await ListTransactionsUseCase(repo).execute(tags=["miete"])
    assert len(result) == 1
    assert "miete" in result[0].tags


# ---------------------------------------------------------------------------
# DeleteTransaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_transaction_current_month(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(_expense_input(tx_date=date.today()))
    await DeleteTransactionUseCase(repo).execute(t.id)
    assert repo._transactions.get(t.id) is None


@pytest.mark.asyncio
async def test_delete_transaction_not_found(repo: InMemoryCostRepository) -> None:
    with pytest.raises(EntityNotFoundError):
        await DeleteTransactionUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_transaction_past_month_rejected(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(
        _expense_input(tx_date=date(2025, 1, 1))
    )
    with pytest.raises(InvalidOperationError, match="past months"):
        await DeleteTransactionUseCase(repo).execute(t.id)


# ---------------------------------------------------------------------------
# Recurring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_recurring(repo: InMemoryCostRepository) -> None:
    inp = CreateRecurringInput(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.MONTHLY,
        day_of_month=1,
    )
    r = await CreateRecurringUseCase(repo).execute(inp)
    assert r.is_active is True
    assert repo._recurring[r.id].title == "Miete"


@pytest.mark.asyncio
async def test_list_recurring_active_only(repo: InMemoryCostRepository) -> None:
    create = CreateRecurringUseCase(repo)
    r1 = await create.execute(
        CreateRecurringInput(
            title="Aktiv",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    r2 = await create.execute(
        CreateRecurringInput(
            title="Inaktiv",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    repo._recurring[r2.id].is_active = False

    active = await ListRecurringUseCase(repo).execute(active_only=True)
    assert len(active) == 1
    assert active[0].id == r1.id


@pytest.mark.asyncio
async def test_delete_recurring_not_found(repo: InMemoryCostRepository) -> None:
    with pytest.raises(EntityNotFoundError):
        await DeleteRecurringUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_recurring_success(repo: InMemoryCostRepository) -> None:
    r = await CreateRecurringUseCase(repo).execute(
        CreateRecurringInput(
            title="Netflix",
            amount=Decimal("17.99"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    await DeleteRecurringUseCase(repo).execute(r.id)
    assert repo._recurring.get(r.id) is None


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_tags_union(repo: InMemoryCostRepository) -> None:
    await CreateTransactionUseCase(repo).execute(_expense_input(tags=["miete"]))
    await CreateRecurringUseCase(repo).execute(
        CreateRecurringInput(
            title="Strom",
            amount=Decimal("80.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
            tags=["versicherung"],
        )
    )
    tags = await ListCostTagsUseCase(repo).execute()
    assert "miete" in tags
    assert "versicherung" in tags
    assert tags == sorted(tags)
