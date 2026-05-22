from __future__ import annotations

import pytest

from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


def test_transaction_type_values() -> None:
    assert TransactionType.INCOME.value == "income"
    assert TransactionType.EXPENSE.value == "expense"
    assert TransactionType.TRANSFER.value == "transfer"
    assert TransactionType.STOCK.value == "stock"


def test_recurrence_interval_values() -> None:
    assert RecurrenceInterval.WEEKLY.value == "weekly"
    assert RecurrenceInterval.MONTHLY.value == "monthly"
    assert RecurrenceInterval.YEARLY.value == "yearly"


def test_transaction_type_from_string() -> None:
    assert TransactionType("income") is TransactionType.INCOME
    assert TransactionType("expense") is TransactionType.EXPENSE
    assert TransactionType("transfer") is TransactionType.TRANSFER
    assert TransactionType("stock") is TransactionType.STOCK


def test_transaction_type_invalid() -> None:
    with pytest.raises(ValueError):
        TransactionType("unknown")


def test_recurrence_interval_from_string() -> None:
    assert RecurrenceInterval("monthly") is RecurrenceInterval.MONTHLY
