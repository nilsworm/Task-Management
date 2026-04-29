from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------


def test_transaction_create_minimal() -> None:
    t = Transaction.create(
        title="Gehalt",
        amount=Decimal("3000.00"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 1),
    )
    assert t.title == "Gehalt"
    assert t.amount == Decimal("3000.00")
    assert t.transaction_type is TransactionType.INCOME
    assert t.tags == []
    assert t.description == ""
    assert t.recurring_source_id is None


def test_transaction_normalizes_tags() -> None:
    t = Transaction.create(
        title="Einkauf",
        amount=Decimal("50.00"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 4, 15),
        tags=["  Miete  ", "LEBENSMITTEL", "miete"],  # duplicate after normalize
    )
    assert t.tags == ["miete", "lebensmittel"]


def test_transaction_rejects_empty_title() -> None:
    with pytest.raises(ValueError, match="title cannot be empty"):
        Transaction.create(
            title="   ",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 1),
        )


def test_transaction_rejects_zero_amount() -> None:
    with pytest.raises(ValueError, match="amount must be greater than 0"):
        Transaction.create(
            title="Test",
            amount=Decimal("0"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 1),
        )


def test_transaction_rejects_negative_amount() -> None:
    with pytest.raises(ValueError, match="amount must be greater than 0"):
        Transaction.create(
            title="Test",
            amount=Decimal("-5.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 1),
        )


def test_transaction_rejects_empty_tag() -> None:
    with pytest.raises(ValueError, match="tag cannot be empty"):
        Transaction.create(
            title="Test",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 1),
            tags=["valid", ""],
        )


def test_transaction_rejects_tag_too_long() -> None:
    with pytest.raises(ValueError, match="tag cannot exceed 50 characters"):
        Transaction.create(
            title="Test",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 1),
            tags=["a" * 51],
        )


def test_transaction_title_stripped() -> None:
    t = Transaction.create(
        title="  Miete  ",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 4, 1),
    )
    assert t.title == "Miete"


# ---------------------------------------------------------------------------
# RecurringTransaction
# ---------------------------------------------------------------------------


def test_recurring_create_minimal() -> None:
    r = RecurringTransaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.MONTHLY,
        day_of_month=1,
    )
    assert r.title == "Miete"
    assert r.interval is RecurrenceInterval.MONTHLY
    assert r.day_of_month == 1
    assert r.is_active is True


def test_recurring_invalid_day_of_month_zero() -> None:
    with pytest.raises(ValueError, match="day_of_month must be between 1 and 28"):
        RecurringTransaction.create(
            title="Test",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
            day_of_month=0,
        )


def test_recurring_invalid_day_of_month_29() -> None:
    with pytest.raises(ValueError, match="day_of_month must be between 1 and 28"):
        RecurringTransaction.create(
            title="Test",
            amount=Decimal("100.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
            day_of_month=29,
        )


def test_recurring_day_of_month_none_allowed() -> None:
    r = RecurringTransaction.create(
        title="Wöchentlich",
        amount=Decimal("50.00"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.WEEKLY,
    )
    assert r.day_of_month is None


def test_recurring_normalizes_tags() -> None:
    r = RecurringTransaction.create(
        title="Netflix",
        amount=Decimal("17.99"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.MONTHLY,
        tags=["Freizeit", "FREIZEIT"],
    )
    assert r.tags == ["freizeit"]
