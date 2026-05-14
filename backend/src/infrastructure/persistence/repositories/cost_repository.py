from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, extract, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import TransactionType
from src.infrastructure.persistence.cost_mappers import (
    recurring_from_model,
    recurring_to_model,
    transaction_from_model,
    transaction_to_model,
)
from src.infrastructure.persistence.models.cost_models import (
    RecurringTransactionModel,
    TransactionModel,
)


class PostgresCostRepository(ICostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_transaction(self, transaction: Transaction) -> None:
        model = transaction_to_model(transaction)
        await self._session.merge(model)
        await self._session.commit()

    async def save_transactions_bulk(self, transactions: list[Transaction]) -> None:
        for transaction in transactions:
            await self._session.merge(transaction_to_model(transaction))
        await self._session.commit()

    async def get_transaction(self, transaction_id: uuid.UUID) -> Transaction | None:
        result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.id == transaction_id)
        )
        model = result.scalar_one_or_none()
        return transaction_from_model(model) if model else None

    async def list_transactions(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]:
        stmt = select(TransactionModel).order_by(TransactionModel.date.desc())

        if year is not None:
            stmt = stmt.where(extract("year", TransactionModel.date) == year)
        if month is not None:
            stmt = stmt.where(extract("month", TransactionModel.date) == month)
        if transaction_type is not None:
            stmt = stmt.where(TransactionModel.transaction_type == transaction_type.value)
        if tags:
            stmt = stmt.where(TransactionModel.tags.overlap(tags))

        result = await self._session.execute(stmt)
        return [transaction_from_model(m) for m in result.scalars().all()]

    async def delete_transaction(self, transaction_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(TransactionModel).where(TransactionModel.id == transaction_id)
        )
        await self._session.commit()

    async def save_recurring(self, recurring: RecurringTransaction) -> None:
        model = recurring_to_model(recurring)
        await self._session.merge(model)
        await self._session.commit()

    async def get_recurring(self, recurring_id: uuid.UUID) -> RecurringTransaction | None:
        result = await self._session.execute(
            select(RecurringTransactionModel).where(
                RecurringTransactionModel.id == recurring_id
            )
        )
        model = result.scalar_one_or_none()
        return recurring_from_model(model) if model else None

    async def list_recurring(self, active_only: bool = False) -> list[RecurringTransaction]:
        stmt = select(RecurringTransactionModel).order_by(
            RecurringTransactionModel.created_at.desc()
        )
        if active_only:
            stmt = stmt.where(RecurringTransactionModel.is_active.is_(True))
        result = await self._session.execute(stmt)
        return [recurring_from_model(m) for m in result.scalars().all()]

    async def delete_recurring(self, recurring_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(RecurringTransactionModel).where(
                RecurringTransactionModel.id == recurring_id
            )
        )
        await self._session.commit()

    async def list_all_tags(self) -> list[str]:
        tx_tags = select(func.unnest(TransactionModel.tags).label("tag"))
        rec_tags = select(func.unnest(RecurringTransactionModel.tags).label("tag"))
        stmt = union(tx_tags, rec_tags).subquery()
        result = await self._session.execute(
            select(stmt.c.tag).where(stmt.c.tag.isnot(None)).order_by(stmt.c.tag)
        )
        return list(result.scalars().all())

    async def create_transaction_from_import(
        self,
        parsed_row: dict[str, Any],
        import_source: str,
    ) -> Transaction:
        """Create and persist a Transaction from parsed CSV row."""
        transaction = Transaction.create(
            title=parsed_row["description"],
            amount=parsed_row["amount"],
            transaction_type=TransactionType(parsed_row["type"].lower()),
            transaction_date=parsed_row["date"],
            import_source=import_source,
        )
        await self.save_transaction(transaction)
        return transaction
