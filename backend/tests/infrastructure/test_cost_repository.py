"""Integration tests for PostgresCostRepository against real Postgres."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType
from src.infrastructure.persistence.repositories.cost_repository import PostgresCostRepository


@pytest.fixture
def repo(db_session: AsyncSession) -> PostgresCostRepository:
    return PostgresCostRepository(db_session)


def _tx(
    title: str = "Miete",
    amount: str = "800.00",
    tx_type: TransactionType = TransactionType.EXPENSE,
    tx_date: date = date(2026, 4, 1),
    tags: list[str] | None = None,
    recurring_source_id: uuid.UUID | None = None,
    import_source: str | None = None,
) -> Transaction:
    return Transaction.create(
        title=title,
        amount=Decimal(amount),
        transaction_type=tx_type,
        transaction_date=tx_date,
        tags=tags or [],
        recurring_source_id=recurring_source_id,
        import_source=import_source,
    )


def _rec(
    title: str = "Miete",
    amount: str = "800.00",
    interval: RecurrenceInterval = RecurrenceInterval.MONTHLY,
    day_of_month: int | None = 1,
    tags: list[str] | None = None,
    active: bool = True,
) -> RecurringTransaction:
    r = RecurringTransaction.create(
        title=title,
        amount=Decimal(amount),
        transaction_type=TransactionType.EXPENSE,
        interval=interval,
        day_of_month=day_of_month,
        tags=tags or [],
        start_date=date(2025, 1, 1),
    )
    r.is_active = active
    return r


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


async def test_save_and_get_transaction(repo: PostgresCostRepository) -> None:
    tx = _tx()
    await repo.save_transaction(tx)
    result = await repo.get_transaction(tx.id)
    assert result is not None
    assert result.id == tx.id
    assert result.title == "Miete"
    assert result.amount == Decimal("800.00")
    assert result.transaction_type is TransactionType.EXPENSE


async def test_get_transaction_missing_returns_none(repo: PostgresCostRepository) -> None:
    assert await repo.get_transaction(uuid.uuid4()) is None


async def test_list_transactions_filter_by_month(repo: PostgresCostRepository) -> None:
    await repo.save_transaction(_tx(tx_date=date(2026, 4, 1)))
    await repo.save_transaction(_tx(tx_date=date(2026, 3, 1)))
    result = await repo.list_transactions(year=2026, month=4)
    assert len(result) == 1
    assert result[0].date == date(2026, 4, 1)


async def test_list_transactions_filter_by_type(repo: PostgresCostRepository) -> None:
    await repo.save_transaction(_tx(tx_type=TransactionType.EXPENSE))
    await repo.save_transaction(_tx(tx_type=TransactionType.INCOME, title="Gehalt"))
    expenses = await repo.list_transactions(transaction_type=TransactionType.EXPENSE)
    assert all(t.transaction_type is TransactionType.EXPENSE for t in expenses)


async def test_list_transactions_filter_by_tags(repo: PostgresCostRepository) -> None:
    await repo.save_transaction(_tx(tags=["miete"]))
    await repo.save_transaction(_tx(tags=["lebensmittel"], title="REWE"))
    result = await repo.list_transactions(tags=["miete"])
    assert len(result) == 1
    assert "miete" in result[0].tags


async def test_delete_transaction(repo: PostgresCostRepository) -> None:
    tx = _tx()
    await repo.save_transaction(tx)
    await repo.delete_transaction(tx.id)
    assert await repo.get_transaction(tx.id) is None


async def test_transaction_preserves_recurring_source_id(repo: PostgresCostRepository) -> None:
    r = _rec()
    await repo.save_recurring(r)
    tx = _tx(recurring_source_id=r.id)
    await repo.save_transaction(tx)
    result = await repo.get_transaction(tx.id)
    assert result is not None
    assert result.recurring_source_id == r.id


async def test_transaction_preserves_import_source(repo: PostgresCostRepository) -> None:
    """Verify import_source field is persisted and retrieved correctly."""
    tx = _tx(import_source="consorsbank")
    await repo.save_transaction(tx)
    result = await repo.get_transaction(tx.id)
    assert result is not None
    assert result.import_source == "consorsbank"


# ---------------------------------------------------------------------------
# Recurring
# ---------------------------------------------------------------------------


async def test_save_and_get_recurring(repo: PostgresCostRepository) -> None:
    r = _rec()
    await repo.save_recurring(r)
    result = await repo.get_recurring(r.id)
    assert result is not None
    assert result.id == r.id
    assert result.title == "Miete"
    assert result.interval is RecurrenceInterval.MONTHLY
    assert result.day_of_month == 1
    assert result.is_active is True


async def test_get_recurring_missing_returns_none(repo: PostgresCostRepository) -> None:
    assert await repo.get_recurring(uuid.uuid4()) is None


async def test_list_recurring_active_only(repo: PostgresCostRepository) -> None:
    await repo.save_recurring(_rec(title="Aktiv", active=True))
    await repo.save_recurring(_rec(title="Inaktiv", active=False))
    active = await repo.list_recurring(active_only=True)
    assert all(r.is_active for r in active)
    assert len(active) == 1


async def test_delete_recurring(repo: PostgresCostRepository) -> None:
    r = _rec()
    await repo.save_recurring(r)
    await repo.delete_recurring(r.id)
    assert await repo.get_recurring(r.id) is None


async def test_recurring_preserves_tags(repo: PostgresCostRepository) -> None:
    r = _rec(tags=["wohnen", "fix"])
    await repo.save_recurring(r)
    result = await repo.get_recurring(r.id)
    assert result is not None
    assert set(result.tags) == {"wohnen", "fix"}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


async def test_list_all_tags_union(repo: PostgresCostRepository) -> None:
    await repo.save_transaction(_tx(tags=["lebensmittel"]))
    await repo.save_recurring(_rec(tags=["wohnen"]))
    tags = await repo.list_all_tags()
    assert "lebensmittel" in tags
    assert "wohnen" in tags
    assert tags == sorted(tags)


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


async def test_create_transaction_from_import_consorsbank(repo: PostgresCostRepository) -> None:
    """Create transaction from parsed Consorsbank CSV row."""
    parsed_row = {
        "date": date(2026, 5, 1),
        "amount": Decimal("500.00"),
        "type": "EXPENSE",
        "description": "Amazon - Laptop",
    }

    transaction = await repo.create_transaction_from_import(parsed_row, "consorsbank")

    assert transaction.import_source == "consorsbank"
    assert transaction.title == "Amazon - Laptop"
    assert transaction.amount == Decimal("500.00")
    assert transaction.transaction_type is TransactionType.EXPENSE
    assert transaction.date == date(2026, 5, 1)

    # Verify persisted in DB
    fetched = await repo.get_transaction(transaction.id)
    assert fetched is not None
    assert fetched.import_source == "consorsbank"
    assert fetched.title == "Amazon - Laptop"


async def test_create_transaction_from_import_trade_republic(repo: PostgresCostRepository) -> None:
    """Create transaction from parsed Trade Republic CSV row."""
    parsed_row = {
        "date": date(2026, 5, 15),
        "amount": Decimal("250.50"),
        "type": "INCOME",
        "description": "Dividend Payment",
    }

    transaction = await repo.create_transaction_from_import(parsed_row, "trade_republic")

    assert transaction.import_source == "trade_republic"
    assert transaction.title == "Dividend Payment"
    assert transaction.amount == Decimal("250.50")
    assert transaction.transaction_type is TransactionType.INCOME
    assert transaction.date == date(2026, 5, 15)

    # Verify persisted in DB
    fetched = await repo.get_transaction(transaction.id)
    assert fetched is not None
    assert fetched.import_source == "trade_republic"


# ---------------------------------------------------------------------------
# Opening Balance
# ---------------------------------------------------------------------------


async def test_get_opening_balance_transaction_exists(repo: PostgresCostRepository) -> None:
    """Retrieve existing opening balance transaction."""
    opening_tx = _tx(
        title="Opening Balance May",
        amount="2000.00",
        tx_type=TransactionType.INCOME,
        tx_date=date(2026, 5, 1),
    )
    opening_tx.is_opening_balance = True
    await repo.save_transaction(opening_tx)

    result = await repo.get_opening_balance_transaction(year=2026, month=5)
    assert result is not None
    assert result.is_opening_balance is True
    assert result.title == "Opening Balance May"


async def test_get_opening_balance_transaction_not_found(repo: PostgresCostRepository) -> None:
    """Return None if no opening balance exists."""
    result = await repo.get_opening_balance_transaction(year=2026, month=5)
    assert result is None


@pytest.mark.asyncio
async def test_transaction_exists_returns_true(repo: PostgresCostRepository) -> None:
    """transaction_exists returns True for a transaction with matching date/amount/description."""
    from datetime import date
    tx = Transaction.create(
        title="Supermarkt",
        amount=Decimal("45.50"),
        transaction_type=TransactionType.EXPENSE,
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


@pytest.mark.asyncio
async def test_update_tags_sets_tags(repo: PostgresCostRepository) -> None:
    """update_tags sets tags on an existing transaction."""
    tx = _tx(title="Rewe", tags=[])
    await repo.save_transaction(tx)
    await repo.update_tags(tx.id, ["lebensmittel", "unnötig"])
    fetched = await repo.get_transaction(tx.id)
    assert fetched is not None
    assert set(fetched.tags) == {"lebensmittel", "unnötig"}
