from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_title(title: str) -> None:
    if not title.strip():
        raise ValueError("title cannot be empty")
    if len(title) > 200:
        raise ValueError("title cannot exceed 200 characters")


def _validate_amount(amount: Decimal) -> None:
    if amount <= Decimal("0"):
        raise ValueError("amount must be greater than 0")


def _normalize_tags(tags: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for tag in tags:
        normalized = tag.strip().lower()
        if not normalized:
            raise ValueError("tag cannot be empty")
        if len(normalized) > 50:
            raise ValueError("tag cannot exceed 50 characters")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


@dataclass
class Transaction:
    id: uuid.UUID
    title: str
    amount: Decimal
    transaction_type: TransactionType
    date: date
    tags: list[str]
    description: str
    recurring_source_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _validate_title(self.title)
        _validate_amount(self.amount)
        self.tags = _normalize_tags(self.tags)

    @classmethod
    def create(
        cls,
        title: str,
        amount: Decimal,
        transaction_type: TransactionType,
        transaction_date: date,
        *,
        tags: list[str] | None = None,
        description: str = "",
        recurring_source_id: uuid.UUID | None = None,
        id: uuid.UUID | None = None,
    ) -> Transaction:
        now = _now()
        return cls(
            id=id or uuid.uuid4(),
            title=title.strip(),
            amount=amount,
            transaction_type=transaction_type,
            date=transaction_date,
            tags=tags or [],
            description=description,
            recurring_source_id=recurring_source_id,
            created_at=now,
            updated_at=now,
        )


@dataclass
class RecurringTransaction:
    id: uuid.UUID
    title: str
    amount: Decimal
    transaction_type: TransactionType
    interval: RecurrenceInterval
    day_of_month: int | None
    tags: list[str]
    is_active: bool
    start_date: date
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _validate_title(self.title)
        _validate_amount(self.amount)
        if self.day_of_month is not None and not (1 <= self.day_of_month <= 28):
            raise ValueError("day_of_month must be between 1 and 28")
        self.tags = _normalize_tags(self.tags)

    @classmethod
    def create(
        cls,
        title: str,
        amount: Decimal,
        transaction_type: TransactionType,
        interval: RecurrenceInterval,
        *,
        day_of_month: int | None = None,
        tags: list[str] | None = None,
        start_date: date | None = None,
        id: uuid.UUID | None = None,
    ) -> RecurringTransaction:
        now = _now()
        return cls(
            id=id or uuid.uuid4(),
            title=title.strip(),
            amount=amount,
            transaction_type=transaction_type,
            interval=interval,
            day_of_month=day_of_month,
            tags=tags or [],
            is_active=True,
            start_date=start_date or date.today(),
            created_at=now,
            updated_at=now,
        )
