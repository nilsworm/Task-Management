from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------


@dataclass
class CreateTransactionInput:
    title: str
    amount: Decimal
    transaction_type: TransactionType
    date: date
    tags: list[str] = field(default_factory=list)
    description: str = ""
    recurring_source_id: uuid.UUID | None = None


class CreateTransactionUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, input: CreateTransactionInput) -> Transaction:
        transaction = Transaction.create(
            title=input.title,
            amount=input.amount,
            transaction_type=input.transaction_type,
            transaction_date=input.date,
            tags=input.tags,
            description=input.description,
            recurring_source_id=input.recurring_source_id,
        )
        await self._repo.save_transaction(transaction)
        return transaction


class ListTransactionsUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]:
        return await self._repo.list_transactions(
            year=year,
            month=month,
            tags=tags,
            transaction_type=transaction_type,
        )


class DeleteTransactionUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, transaction_id: uuid.UUID) -> None:
        transaction = await self._repo.get_transaction(transaction_id)
        if transaction is None:
            raise EntityNotFoundError("Transaction", str(transaction_id))

        today = date.today()
        if (transaction.date.year, transaction.date.month) != (today.year, today.month):
            raise InvalidOperationError(
                "Transactions from past months cannot be deleted"
            )

        await self._repo.delete_transaction(transaction_id)


# ---------------------------------------------------------------------------
# Recurring
# ---------------------------------------------------------------------------


@dataclass
class CreateRecurringInput:
    title: str
    amount: Decimal
    transaction_type: TransactionType
    interval: RecurrenceInterval
    day_of_month: int | None = None
    tags: list[str] = field(default_factory=list)
    start_date: date | None = None


class CreateRecurringUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, input: CreateRecurringInput) -> RecurringTransaction:
        recurring = RecurringTransaction.create(
            title=input.title,
            amount=input.amount,
            transaction_type=input.transaction_type,
            interval=input.interval,
            day_of_month=input.day_of_month,
            tags=input.tags,
            start_date=input.start_date,
        )
        await self._repo.save_recurring(recurring)
        return recurring


class ListRecurringUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, active_only: bool = False) -> list[RecurringTransaction]:
        return await self._repo.list_recurring(active_only=active_only)


class DeleteRecurringUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, recurring_id: uuid.UUID) -> None:
        recurring = await self._repo.get_recurring(recurring_id)
        if recurring is None:
            raise EntityNotFoundError("RecurringTransaction", str(recurring_id))
        await self._repo.delete_recurring(recurring_id)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class ListCostTagsUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self) -> list[str]:
        return await self._repo.list_all_tags()
