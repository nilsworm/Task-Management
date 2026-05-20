from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


def _last_n_months(year: int, month: int, n: int = 6) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    y, m = year, month
    for _ in range(n):
        result.insert(0, (y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return result


@dataclass
class CostSummary:
    year: int
    month: int
    income: Decimal
    expenses: Decimal
    balance: Decimal


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
# Generate Monthly
# ---------------------------------------------------------------------------


class GenerateMonthlyUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, year: int, month: int) -> list[Transaction]:
        recurring = await self._repo.list_recurring(active_only=True)
        if not recurring:
            return []

        existing = await self._repo.list_transactions(year=year, month=month)
        existing_source_ids = {t.recurring_source_id for t in existing if t.recurring_source_id}

        to_create = [r for r in recurring if r.id not in existing_source_ids]
        if not to_create:
            raise InvalidOperationError("Monat wurde bereits generiert")

        created: list[Transaction] = [
            Transaction.create(
                title=r.title,
                amount=r.amount,
                transaction_type=r.transaction_type,
                transaction_date=date(year, month, r.day_of_month or 1),
                tags=r.tags,
                recurring_source_id=r.id,
            )
            for r in to_create
        ]
        await self._repo.save_transactions_bulk(created)
        return created


# ---------------------------------------------------------------------------
# Update Recurring (is_active toggle)
# ---------------------------------------------------------------------------


@dataclass
class UpdateRecurringInput:
    recurring_id: uuid.UUID
    is_active: bool


class UpdateRecurringUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, input: UpdateRecurringInput) -> RecurringTransaction:
        recurring = await self._repo.get_recurring(input.recurring_id)
        if recurring is None:
            raise EntityNotFoundError("RecurringTransaction", str(input.recurring_id))
        recurring.is_active = input.is_active
        recurring.updated_at = datetime.now(timezone.utc)
        await self._repo.save_recurring(recurring)
        return recurring


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class GetCostSummaryUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, year: int, month: int) -> CostSummary:
        transactions = await self._repo.list_transactions(year=year, month=month)
        income = sum(
            (t.amount for t in transactions if t.transaction_type == TransactionType.INCOME),
            Decimal("0"),
        )
        expenses = sum(
            (t.amount for t in transactions if t.transaction_type == TransactionType.EXPENSE),
            Decimal("0"),
        )
        return CostSummary(year=year, month=month, income=income, expenses=expenses, balance=income - expenses)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


class ListCostTagsUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self) -> list[str]:
        return await self._repo.list_all_tags()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@dataclass
class TagBreakdown:
    tag: str
    amount: Decimal


@dataclass
class MonthlyComparison:
    year: int
    month: int
    income: Decimal
    expenses: Decimal


@dataclass
class CostAnalytics:
    expenses_by_tag: list[TagBreakdown]
    monthly_comparison: list[MonthlyComparison]


class GetCostAnalyticsUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(
        self,
        year: int,
        month: int,
        tags: list[str] | None = None,
    ) -> CostAnalytics:
        expenses = await self._repo.list_transactions(
            year=year, month=month, tags=tags, transaction_type=TransactionType.EXPENSE
        )
        tag_totals: dict[str, Decimal] = {}
        for tx in expenses:
            for tag in tx.tags:
                tag_totals[tag] = tag_totals.get(tag, Decimal("0")) + tx.amount
        expenses_by_tag = [
            TagBreakdown(tag=tag, amount=amount)
            for tag, amount in sorted(tag_totals.items(), key=lambda x: x[1], reverse=True)
        ]

        comparison: list[MonthlyComparison] = []
        for y, m in _last_n_months(year, month, n=6):
            txs = await self._repo.list_transactions(year=y, month=m, tags=tags)
            income = sum(
                (t.amount for t in txs if t.transaction_type == TransactionType.INCOME),
                Decimal("0"),
            )
            exps = sum(
                (t.amount for t in txs if t.transaction_type == TransactionType.EXPENSE),
                Decimal("0"),
            )
            comparison.append(MonthlyComparison(year=y, month=m, income=income, expenses=exps))

        return CostAnalytics(expenses_by_tag=expenses_by_tag, monthly_comparison=comparison)


# ---------------------------------------------------------------------------
# Opening Balance
# ---------------------------------------------------------------------------


class CalculateOpeningBalanceUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, year: int, month: int) -> Decimal:
        """Calculate opening balance for a month.

        Opening balance = closing balance of previous month.
        For first month (January with no December), returns 0.

        Returns: Decimal balance
        """
        # Calculate previous month (handle year boundary)
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1

        # Get all transactions from previous month (excluding opening balance)
        prev_transactions = await self._repo.list_transactions(
            year=prev_year, month=prev_month
        )

        # Filter out opening balance transactions
        prev_transactions = [
            t for t in prev_transactions if not t.is_opening_balance
        ]

        # Calculate balance
        income = sum(
            (t.amount for t in prev_transactions if t.transaction_type == TransactionType.INCOME),
            Decimal("0"),
        )
        expenses = sum(
            (t.amount for t in prev_transactions if t.transaction_type == TransactionType.EXPENSE),
            Decimal("0"),
        )

        return income - expenses


class EnsureOpeningBalanceTransactionUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository
        self._calc_balance_uc = CalculateOpeningBalanceUseCase(repository)

    async def execute(self, year: int, month: int) -> Transaction | None:
        """Ensure opening balance transaction exists for month.

        - If month is current month: return None (not yet applicable)
        - If month in future: return None (not applicable)
        - If month in past:
          - Check if opening balance already exists
          - If yes: return existing
          - If no: calculate and create
        """
        today = date.today()

        # Future month only: skip (current month is valid — opening balance = prev month closing)
        if (year, month) > (today.year, today.month):
            return None

        # Check if already exists
        existing = await self._repo.get_opening_balance_transaction(year, month)
        if existing:
            return existing

        # Calculate opening balance
        balance = await self._calc_balance_uc.execute(year, month)

        # No transactions in previous month → no opening balance to record
        if balance == Decimal("0"):
            return None

        # Create transaction with month name
        month_name = date(year, month, 1).strftime("%B")
        opening_tx = Transaction.create(
            title=f"Opening Balance {month_name}",
            amount=abs(balance),
            transaction_type=TransactionType.INCOME if balance >= 0 else TransactionType.EXPENSE,
            transaction_date=date(year, month, 1),
            is_opening_balance=True,
        )

        await self._repo.save_transaction(opening_tx)
        return opening_tx


# ---------------------------------------------------------------------------
# Import Transactions
# ---------------------------------------------------------------------------


@dataclass
class ImportTransactionsInput:
    parsed_rows: list[dict]
    import_source: str


@dataclass
class ImportTransactionsResult:
    imported: int
    skipped: int


class ImportTransactionsUseCase:
    def __init__(self, cost_repo: ICostRepository) -> None:
        self._repo = cost_repo

    async def execute(self, input: ImportTransactionsInput) -> ImportTransactionsResult:
        imported = 0
        skipped = 0
        for row in input.parsed_rows:
            try:
                exists = await self._repo.transaction_exists(
                    row["date"], row["amount"], row["description"]
                )
                if exists:
                    skipped += 1
                else:
                    await self._repo.create_transaction_from_import(row, input.import_source)
                    imported += 1
            except Exception:
                logger.error("Failed to import row: %s", row, exc_info=True)
        return ImportTransactionsResult(imported=imported, skipped=skipped)
