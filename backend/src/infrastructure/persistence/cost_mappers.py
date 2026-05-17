from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType
from src.infrastructure.persistence.models.cost_models import (
    RecurringTransactionModel,
    TransactionModel,
)


def _utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def transaction_to_model(t: Transaction) -> TransactionModel:
    return TransactionModel(
        id=t.id,
        title=t.title,
        amount=t.amount,
        transaction_type=t.transaction_type.value,
        date=t.date,
        tags=t.tags,
        description=t.description,
        recurring_source_id=t.recurring_source_id,
        import_source=t.import_source,
        is_opening_balance=t.is_opening_balance,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def transaction_from_model(m: TransactionModel) -> Transaction:
    return Transaction(
        id=m.id,
        title=m.title,
        amount=Decimal(str(m.amount)),
        transaction_type=TransactionType(m.transaction_type),
        date=m.date,
        tags=list(m.tags or []),
        description=m.description,
        recurring_source_id=m.recurring_source_id,
        import_source=m.import_source,
        is_opening_balance=m.is_opening_balance,
        created_at=_utc(m.created_at),
        updated_at=_utc(m.updated_at),
    )


def recurring_to_model(r: RecurringTransaction) -> RecurringTransactionModel:
    return RecurringTransactionModel(
        id=r.id,
        title=r.title,
        amount=r.amount,
        transaction_type=r.transaction_type.value,
        interval=r.interval.value,
        day_of_month=r.day_of_month,
        tags=r.tags,
        is_active=r.is_active,
        start_date=r.start_date,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def recurring_from_model(m: RecurringTransactionModel) -> RecurringTransaction:
    return RecurringTransaction(
        id=m.id,
        title=m.title,
        amount=Decimal(str(m.amount)),
        transaction_type=TransactionType(m.transaction_type),
        interval=RecurrenceInterval(m.interval),
        day_of_month=m.day_of_month,
        tags=list(m.tags or []),
        is_active=m.is_active,
        start_date=m.start_date,
        created_at=_utc(m.created_at),
        updated_at=_utc(m.updated_at),
    )
