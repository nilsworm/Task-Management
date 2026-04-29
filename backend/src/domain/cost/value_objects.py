from __future__ import annotations

import enum


class TransactionType(enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class RecurrenceInterval(enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
