from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import TransactionType


class ICostRepository(ABC):
    @abstractmethod
    async def save_transaction(self, transaction: Transaction) -> None: ...

    @abstractmethod
    async def get_transaction(self, transaction_id: uuid.UUID) -> Transaction | None: ...

    @abstractmethod
    async def list_transactions(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]: ...

    @abstractmethod
    async def delete_transaction(self, transaction_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def save_recurring(self, recurring: RecurringTransaction) -> None: ...

    @abstractmethod
    async def get_recurring(self, recurring_id: uuid.UUID) -> RecurringTransaction | None: ...

    @abstractmethod
    async def list_recurring(self, active_only: bool = False) -> list[RecurringTransaction]: ...

    @abstractmethod
    async def delete_recurring(self, recurring_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_all_tags(self) -> list[str]: ...
