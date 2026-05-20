from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date as date_type
from decimal import Decimal

from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import TransactionType


class ICostRepository(ABC):
    @abstractmethod
    async def save_transaction(self, transaction: Transaction) -> None: ...

    @abstractmethod
    async def save_transactions_bulk(self, transactions: list[Transaction]) -> None: ...

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

    @abstractmethod
    async def create_transaction_from_import(
        self,
        parsed_row: dict,
        import_source: str,
    ) -> Transaction:
        """Create and persist a Transaction from parsed CSV row.

        Args:
            parsed_row: Dict with keys {date, amount, type, description}.
                - date: datetime.date
                - amount: Decimal
                - type: str ("INCOME" or "EXPENSE")
                - description: str
            import_source: Source identifier (e.g., "consorsbank", "trade_republic")

        Returns:
            The persisted Transaction entity.
        """
        ...

    @abstractmethod
    async def get_opening_balance_transaction(
        self, year: int, month: int
    ) -> Transaction | None:
        """Get opening balance transaction for month (if exists).

        Args:
            year: Year (e.g., 2026)
            month: Month (1-12)

        Returns: Opening balance Transaction or None
        """
        ...

    @abstractmethod
    async def transaction_exists(
        self, transaction_date: date_type, amount: Decimal, description: str
    ) -> bool:
        """Check if a transaction with the same date, amount, and description already exists.

        Used for deduplication during CSV import.
        """
        ...
