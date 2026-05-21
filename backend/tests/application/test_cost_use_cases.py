from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.application.use_cases.cost_use_cases import (
    CalculateOpeningBalanceUseCase,
    CreateRecurringInput,
    CreateRecurringUseCase,
    CreateTransactionInput,
    CreateTransactionUseCase,
    DeleteRecurringUseCase,
    DeleteTransactionUseCase,
    GenerateMonthlyUseCase,
    GetCostSummaryUseCase,
    ListCostTagsUseCase,
    ListRecurringUseCase,
    ListTransactionsUseCase,
    UpdateRecurringInput,
    UpdateRecurringUseCase,
)
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


# ---------------------------------------------------------------------------
# InMemory stub
# ---------------------------------------------------------------------------


class InMemoryCostRepository(ICostRepository):
    def __init__(self) -> None:
        self._transactions: dict[uuid.UUID, Transaction] = {}
        self._recurring: dict[uuid.UUID, RecurringTransaction] = {}

    async def save_transaction(self, transaction: Transaction) -> None:
        self._transactions[transaction.id] = transaction

    async def save_transactions_bulk(self, transactions: list[Transaction]) -> None:
        for transaction in transactions:
            self._transactions[transaction.id] = transaction

    async def get_transaction(self, transaction_id: uuid.UUID) -> Transaction | None:
        return self._transactions.get(transaction_id)

    async def list_transactions(
        self,
        year: int | None = None,
        month: int | None = None,
        tags: list[str] | None = None,
        transaction_type: TransactionType | None = None,
    ) -> list[Transaction]:
        result = list(self._transactions.values())
        if year is not None:
            result = [t for t in result if t.date.year == year]
        if month is not None:
            result = [t for t in result if t.date.month == month]
        if transaction_type is not None:
            result = [t for t in result if t.transaction_type == transaction_type]
        if tags:
            result = [t for t in result if any(tag in t.tags for tag in tags)]
        return sorted(result, key=lambda t: t.date, reverse=True)

    async def delete_transaction(self, transaction_id: uuid.UUID) -> None:
        self._transactions.pop(transaction_id, None)

    async def save_recurring(self, recurring: RecurringTransaction) -> None:
        self._recurring[recurring.id] = recurring

    async def get_recurring(self, recurring_id: uuid.UUID) -> RecurringTransaction | None:
        return self._recurring.get(recurring_id)

    async def list_recurring(self, active_only: bool = False) -> list[RecurringTransaction]:
        result = list(self._recurring.values())
        if active_only:
            result = [r for r in result if r.is_active]
        return result

    async def delete_recurring(self, recurring_id: uuid.UUID) -> None:
        self._recurring.pop(recurring_id, None)

    async def list_all_tags(self) -> list[str]:
        tags: set[str] = set()
        for t in self._transactions.values():
            tags.update(t.tags)
        for r in self._recurring.values():
            tags.update(r.tags)
        return sorted(tags)

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

    async def get_opening_balance_transaction(
        self, year: int, month: int
    ) -> Transaction | None:
        """Get opening balance transaction for month (if exists)."""
        for t in self._transactions.values():
            if t.date.year == year and t.date.month == month and t.is_opening_balance:
                return t
        return None

    async def transaction_exists(
        self, transaction_date: date, amount: Decimal, description: str
    ) -> bool:
        return any(
            t.date == transaction_date and t.amount == amount and t.title == description
            for t in self._transactions.values()
        )

    async def reset_all(self) -> None:
        self._transactions.clear()
        self._recurring.clear()

    @property
    def transactions(self) -> list[Transaction]:
        """Expose transactions list for testing."""
        return list(self._transactions.values())


@pytest.fixture
def repo() -> InMemoryCostRepository:
    return InMemoryCostRepository()


def _expense_input(
    title: str = "Miete",
    amount: str = "800.00",
    tx_date: date | None = None,
    tags: list[str] | None = None,
) -> CreateTransactionInput:
    return CreateTransactionInput(
        title=title,
        amount=Decimal(amount),
        transaction_type=TransactionType.EXPENSE,
        date=tx_date or date.today(),
        tags=tags or [],
    )


def _income_input(title: str = "Gehalt", amount: str = "3000.00") -> CreateTransactionInput:
    return CreateTransactionInput(
        title=title,
        amount=Decimal(amount),
        transaction_type=TransactionType.INCOME,
        date=date.today(),
    )


# ---------------------------------------------------------------------------
# CreateTransaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_transaction_stores_entity(repo: InMemoryCostRepository) -> None:
    uc = CreateTransactionUseCase(repo)
    t = await uc.execute(_expense_input())
    assert repo._transactions[t.id].title == "Miete"


@pytest.mark.asyncio
async def test_create_transaction_returns_entity(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(_income_input())
    assert t.transaction_type is TransactionType.INCOME
    assert t.amount == Decimal("3000.00")


# ---------------------------------------------------------------------------
# ListTransactions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_transactions_empty(repo: InMemoryCostRepository) -> None:
    result = await ListTransactionsUseCase(repo).execute()
    assert result == []


@pytest.mark.asyncio
async def test_list_transactions_filter_by_month(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(tx_date=date(2026, 4, 1)))
    await create.execute(_expense_input(tx_date=date(2026, 3, 1)))

    result = await ListTransactionsUseCase(repo).execute(year=2026, month=4)
    assert len(result) == 1
    assert result[0].date == date(2026, 4, 1)


@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input())
    await create.execute(_income_input())

    expenses = await ListTransactionsUseCase(repo).execute(
        transaction_type=TransactionType.EXPENSE
    )
    assert all(t.transaction_type is TransactionType.EXPENSE for t in expenses)
    assert len(expenses) == 1


@pytest.mark.asyncio
async def test_list_transactions_filter_by_tag(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(tags=["miete"]))
    await create.execute(_expense_input(tags=["lebensmittel"]))

    result = await ListTransactionsUseCase(repo).execute(tags=["miete"])
    assert len(result) == 1
    assert "miete" in result[0].tags


# ---------------------------------------------------------------------------
# DeleteTransaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_transaction_current_month(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(_expense_input(tx_date=date.today()))
    await DeleteTransactionUseCase(repo).execute(t.id)
    assert repo._transactions.get(t.id) is None


@pytest.mark.asyncio
async def test_delete_transaction_not_found(repo: InMemoryCostRepository) -> None:
    with pytest.raises(EntityNotFoundError):
        await DeleteTransactionUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_transaction_past_month_rejected(repo: InMemoryCostRepository) -> None:
    t = await CreateTransactionUseCase(repo).execute(
        _expense_input(tx_date=date(2025, 1, 1))
    )
    with pytest.raises(InvalidOperationError, match="past months"):
        await DeleteTransactionUseCase(repo).execute(t.id)


# ---------------------------------------------------------------------------
# Recurring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_recurring(repo: InMemoryCostRepository) -> None:
    inp = CreateRecurringInput(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.MONTHLY,
        day_of_month=1,
    )
    r = await CreateRecurringUseCase(repo).execute(inp)
    assert r.is_active is True
    assert repo._recurring[r.id].title == "Miete"


@pytest.mark.asyncio
async def test_list_recurring_active_only(repo: InMemoryCostRepository) -> None:
    create = CreateRecurringUseCase(repo)
    r1 = await create.execute(
        CreateRecurringInput(
            title="Aktiv",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    r2 = await create.execute(
        CreateRecurringInput(
            title="Inaktiv",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    repo._recurring[r2.id].is_active = False

    active = await ListRecurringUseCase(repo).execute(active_only=True)
    assert len(active) == 1
    assert active[0].id == r1.id


@pytest.mark.asyncio
async def test_delete_recurring_not_found(repo: InMemoryCostRepository) -> None:
    with pytest.raises(EntityNotFoundError):
        await DeleteRecurringUseCase(repo).execute(uuid.uuid4())


@pytest.mark.asyncio
async def test_delete_recurring_success(repo: InMemoryCostRepository) -> None:
    r = await CreateRecurringUseCase(repo).execute(
        CreateRecurringInput(
            title="Netflix",
            amount=Decimal("17.99"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
        )
    )
    await DeleteRecurringUseCase(repo).execute(r.id)
    assert repo._recurring.get(r.id) is None


# ---------------------------------------------------------------------------
# GenerateMonthly
# ---------------------------------------------------------------------------


def _recurring_input(title: str = "Miete", day: int | None = 1) -> CreateRecurringInput:
    return CreateRecurringInput(
        title=title,
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        interval=RecurrenceInterval.MONTHLY,
        day_of_month=day,
    )


@pytest.mark.asyncio
async def test_generate_monthly_creates_transactions(repo: InMemoryCostRepository) -> None:
    await CreateRecurringUseCase(repo).execute(_recurring_input("Miete", day=1))
    await CreateRecurringUseCase(repo).execute(_recurring_input("Strom", day=15))

    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert len(created) == 2
    titles = {t.title for t in created}
    assert titles == {"Miete", "Strom"}


@pytest.mark.asyncio
async def test_generate_monthly_uses_day_of_month(repo: InMemoryCostRepository) -> None:
    await CreateRecurringUseCase(repo).execute(_recurring_input("Miete", day=3))
    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert created[0].date == date(2026, 5, 3)


@pytest.mark.asyncio
async def test_generate_monthly_falls_back_to_day_1(repo: InMemoryCostRepository) -> None:
    await CreateRecurringUseCase(repo).execute(_recurring_input("Strom", day=None))
    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert created[0].date == date(2026, 5, 1)


@pytest.mark.asyncio
async def test_generate_monthly_sets_recurring_source_id(repo: InMemoryCostRepository) -> None:
    r = await CreateRecurringUseCase(repo).execute(_recurring_input())
    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert created[0].recurring_source_id == r.id


@pytest.mark.asyncio
async def test_generate_monthly_idempotent_no_duplicate(repo: InMemoryCostRepository) -> None:
    await CreateRecurringUseCase(repo).execute(_recurring_input())
    await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)

    with pytest.raises(InvalidOperationError, match="bereits generiert"):
        await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)

    transactions = await repo.list_transactions(year=2026, month=5)
    assert len(transactions) == 1


@pytest.mark.asyncio
async def test_generate_monthly_skips_already_generated(repo: InMemoryCostRepository) -> None:
    r1 = await CreateRecurringUseCase(repo).execute(_recurring_input("Miete"))
    await CreateRecurringUseCase(repo).execute(_recurring_input("Strom"))

    # Manually create only the Miete transaction
    await repo.save_transaction(Transaction.create(
        "Miete", Decimal("800.00"), TransactionType.EXPENSE,
        date(2026, 5, 1), recurring_source_id=r1.id,
    ))

    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert len(created) == 1
    assert created[0].title == "Strom"


@pytest.mark.asyncio
async def test_generate_monthly_empty_recurring_returns_empty(repo: InMemoryCostRepository) -> None:
    result = await GenerateMonthlyUseCase(repo).execute(year=2026, month=5)
    assert result == []


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_empty_month(repo: InMemoryCostRepository) -> None:
    summary = await GetCostSummaryUseCase(repo).execute(year=2026, month=4)
    assert summary.income == Decimal("0")
    assert summary.expenses == Decimal("0")
    assert summary.balance == Decimal("0")


@pytest.mark.asyncio
async def test_summary_calculates_totals(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_income_input(amount="3000.00"))
    await create.execute(_expense_input(amount="800.00"))
    today = date.today()
    summary = await GetCostSummaryUseCase(repo).execute(year=today.year, month=today.month)
    assert summary.income == Decimal("3000.00")
    assert summary.expenses == Decimal("800.00")
    assert summary.balance == Decimal("2200.00")


@pytest.mark.asyncio
async def test_summary_only_counts_given_month(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(amount="500.00", tx_date=date(2026, 4, 1)))
    await create.execute(_expense_input(amount="999.00", tx_date=date(2026, 3, 1)))
    summary = await GetCostSummaryUseCase(repo).execute(year=2026, month=4)
    assert summary.expenses == Decimal("500.00")


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_all_tags_union(repo: InMemoryCostRepository) -> None:
    await CreateTransactionUseCase(repo).execute(_expense_input(tags=["miete"]))
    await CreateRecurringUseCase(repo).execute(
        CreateRecurringInput(
            title="Strom",
            amount=Decimal("80.00"),
            transaction_type=TransactionType.EXPENSE,
            interval=RecurrenceInterval.MONTHLY,
            tags=["versicherung"],
        )
    )
    tags = await ListCostTagsUseCase(repo).execute()
    assert "miete" in tags
    assert "versicherung" in tags
    assert tags == sorted(tags)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analytics_expenses_by_tag(repo: InMemoryCostRepository) -> None:
    now = date.today()
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(amount="100.00", tags=["lebensmittel"], tx_date=now))
    await create.execute(_expense_input(amount="200.00", tags=["miete"], tx_date=now))
    await create.execute(_expense_input(amount="50.00", tags=["lebensmittel"], tx_date=now))

    from src.application.use_cases.cost_use_cases import GetCostAnalyticsUseCase
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=now.year, month=now.month)

    by_tag = {tb.tag: tb.amount for tb in analytics.expenses_by_tag}
    assert by_tag["lebensmittel"] == Decimal("150.00")
    assert by_tag["miete"] == Decimal("200.00")
    # sorted descending by amount
    amounts = [tb.amount for tb in analytics.expenses_by_tag]
    assert amounts == sorted(amounts, reverse=True)


@pytest.mark.asyncio
async def test_analytics_excludes_income_from_by_tag(repo: InMemoryCostRepository) -> None:
    now = date.today()
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(amount="100.00", tags=["kosten"], tx_date=now))
    # income should not appear in expenses_by_tag
    await create.execute(
        CreateTransactionInput(
            title="Gehalt", amount=Decimal("3000.00"),
            transaction_type=TransactionType.INCOME,
            date=now, tags=["gehalt"],
        )
    )
    from src.application.use_cases.cost_use_cases import GetCostAnalyticsUseCase
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=now.year, month=now.month)
    tags = [tb.tag for tb in analytics.expenses_by_tag]
    assert "gehalt" not in tags
    assert "kosten" in tags


@pytest.mark.asyncio
async def test_analytics_monthly_comparison_has_six_entries(repo: InMemoryCostRepository) -> None:
    from src.application.use_cases.cost_use_cases import GetCostAnalyticsUseCase
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=2026, month=4)
    assert len(analytics.monthly_comparison) == 6
    # last entry is the requested month
    assert analytics.monthly_comparison[-1].year == 2026
    assert analytics.monthly_comparison[-1].month == 4


@pytest.mark.asyncio
async def test_analytics_monthly_comparison_sums_correctly(repo: InMemoryCostRepository) -> None:
    create = CreateTransactionUseCase(repo)
    await create.execute(_expense_input(amount="400.00", tx_date=date(2026, 4, 10)))
    await create.execute(
        CreateTransactionInput(
            title="Gehalt", amount=Decimal("3000.00"),
            transaction_type=TransactionType.INCOME, date=date(2026, 4, 1), tags=[],
        )
    )
    from src.application.use_cases.cost_use_cases import GetCostAnalyticsUseCase
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=2026, month=4)
    april = analytics.monthly_comparison[-1]
    assert april.expenses == Decimal("400.00")
    assert april.income == Decimal("3000.00")


# ---------------------------------------------------------------------------
# UpdateRecurring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_recurring_deactivates(repo: InMemoryCostRepository) -> None:
    r = await CreateRecurringUseCase(repo).execute(_recurring_input())
    assert r.is_active is True
    updated = await UpdateRecurringUseCase(repo).execute(
        UpdateRecurringInput(recurring_id=r.id, is_active=False)
    )
    assert updated.is_active is False
    assert repo._recurring[r.id].is_active is False


@pytest.mark.asyncio
async def test_update_recurring_reactivates(repo: InMemoryCostRepository) -> None:
    r = await CreateRecurringUseCase(repo).execute(_recurring_input())
    repo._recurring[r.id].is_active = False
    updated = await UpdateRecurringUseCase(repo).execute(
        UpdateRecurringInput(recurring_id=r.id, is_active=True)
    )
    assert updated.is_active is True


@pytest.mark.asyncio
async def test_update_recurring_not_found(repo: InMemoryCostRepository) -> None:
    with pytest.raises(EntityNotFoundError):
        await UpdateRecurringUseCase(repo).execute(
            UpdateRecurringInput(recurring_id=uuid.uuid4(), is_active=False)
        )


@pytest.mark.asyncio
async def test_generate_monthly_uses_bulk_save(repo: InMemoryCostRepository) -> None:
    await CreateRecurringUseCase(repo).execute(_recurring_input("Miete", day=1))
    await CreateRecurringUseCase(repo).execute(_recurring_input("Strom", day=15))
    created = await GenerateMonthlyUseCase(repo).execute(year=2026, month=6)
    assert len(created) == 2
    assert len(repo._transactions) == 2


# ---------------------------------------------------------------------------
# Opening Balance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_calculate_opening_balance_past_month() -> None:
    """Calculate opening balance (closing balance of previous month)."""
    repo = InMemoryCostRepository()
    # April: +5000 income, -3000 expense = +2000 balance
    await repo.save_transaction(Transaction.create(
        title="Salary",
        amount=Decimal("5000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 1),
    ))
    await repo.save_transaction(Transaction.create(
        title="Rent",
        amount=Decimal("3000"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 4, 15),
    ))

    uc = CalculateOpeningBalanceUseCase(repo)
    result = await uc.execute(year=2026, month=5)

    # Opening balance for May = closing balance of April = 2000
    assert result == Decimal("2000")


@pytest.mark.asyncio
async def test_calculate_opening_balance_includes_prev_opening_balance() -> None:
    """Opening balance of month N includes the opening balance of month N-1 (chain preserved)."""
    repo = InMemoryCostRepository()
    # April has its own opening balance of 4000 (carried from March)
    await repo.save_transaction(Transaction.create(
        title="Opening Balance April",
        amount=Decimal("4000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 1),
        is_opening_balance=True,
    ))
    # April real transactions: +1000 income, -500 expense
    await repo.save_transaction(Transaction.create(
        title="Salary",
        amount=Decimal("1000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 10),
    ))
    await repo.save_transaction(Transaction.create(
        title="Rent",
        amount=Decimal("500"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 4, 15),
    ))

    uc = CalculateOpeningBalanceUseCase(repo)
    result = await uc.execute(year=2026, month=5)

    # May opening balance = 4000 + 1000 - 500 = 4500 (full April closing balance)
    assert result == Decimal("4500")


@pytest.mark.asyncio
async def test_calculate_opening_balance_first_month() -> None:
    """First month (no previous) has opening balance 0."""
    repo = InMemoryCostRepository()
    # No April transactions

    uc = CalculateOpeningBalanceUseCase(repo)
    result = await uc.execute(year=2026, month=5)

    assert result == Decimal("0")


# ---------------------------------------------------------------------------
# Ensure Opening Balance
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_opening_balance_creates_for_past_month() -> None:
    """Create opening balance transaction for past month."""
    repo = InMemoryCostRepository()
    # March: +5000 income, -3000 expense = +2000 balance
    await repo.save_transaction(Transaction.create(
        title="Salary",
        amount=Decimal("5000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 3, 1),
    ))
    await repo.save_transaction(Transaction.create(
        title="Rent",
        amount=Decimal("3000"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 3, 15),
    ))

    from src.application.use_cases.cost_use_cases import EnsureOpeningBalanceTransactionUseCase
    uc = EnsureOpeningBalanceTransactionUseCase(repo)
    result = await uc.execute(year=2026, month=4)

    # Should create opening balance transaction
    assert result is not None
    assert result.is_opening_balance is True
    assert result.title == "Opening Balance April"
    assert result.amount == Decimal("2000")
    assert result.transaction_type == TransactionType.INCOME
    assert result.date == date(2026, 4, 1)


@pytest.mark.asyncio
async def test_ensure_opening_balance_skips_future_month() -> None:
    """Don't create opening balance for future months."""
    repo = InMemoryCostRepository()
    today = date.today()
    future_year = today.year + 1

    from src.application.use_cases.cost_use_cases import EnsureOpeningBalanceTransactionUseCase
    uc = EnsureOpeningBalanceTransactionUseCase(repo)
    result = await uc.execute(year=future_year, month=today.month)

    assert result is None
    assert len(repo.transactions) == 0


@pytest.mark.asyncio
async def test_ensure_opening_balance_creates_for_current_month() -> None:
    """Create opening balance for current month using previous month's closing balance."""
    repo = InMemoryCostRepository()
    today = date.today()
    prev_month = today.month - 1 or 12
    prev_year = today.year if today.month > 1 else today.year - 1

    await repo.save_transaction(Transaction.create(
        title="Salary",
        amount=Decimal("3000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(prev_year, prev_month, 1),
    ))

    from src.application.use_cases.cost_use_cases import EnsureOpeningBalanceTransactionUseCase
    uc = EnsureOpeningBalanceTransactionUseCase(repo)
    result = await uc.execute(year=today.year, month=today.month)

    assert result is not None
    assert result.is_opening_balance is True
    assert result.amount == Decimal("3000")


@pytest.mark.asyncio
async def test_ensure_opening_balance_idempotent() -> None:
    """Don't recreate if opening balance already exists."""
    existing_tx = Transaction.create(
        title="Opening Balance April",
        amount=Decimal("2000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 1),
        is_opening_balance=True,
    )

    repo = InMemoryCostRepository()
    await repo.save_transaction(existing_tx)

    from src.application.use_cases.cost_use_cases import EnsureOpeningBalanceTransactionUseCase
    uc = EnsureOpeningBalanceTransactionUseCase(repo)
    result = await uc.execute(year=2026, month=4)

    # Should return existing
    assert result == existing_tx
    # Should only have the one transaction we added
    assert len(repo.transactions) == 1


# ---------------------------------------------------------------------------
# ListTransactions — opening balance is a router concern, not a UseCase concern
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_transactions_does_not_create_opening_balance() -> None:
    """ListTransactionsUseCase has no side-effects — opening balance is ensured at router level."""
    repo = InMemoryCostRepository()

    await repo.save_transaction(Transaction.create(
        title="Salary",
        amount=Decimal("5000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 4, 1),
    ))

    uc = ListTransactionsUseCase(repo)
    result = await uc.execute(year=2026, month=5)

    # UseCase itself does not create opening balance transactions
    assert all(not t.is_opening_balance for t in result)
    assert len(result) == 0  # No May transactions exist yet


# ---------------------------------------------------------------------------
# transaction_exists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_transaction_exists_returns_true_for_existing(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns True when a transaction with same date/amount/description exists."""
    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Miete")

    assert result is True


@pytest.mark.asyncio
async def test_transaction_exists_returns_false_for_nonexistent(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns False when no matching transaction exists."""
    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Miete")

    assert result is False


@pytest.mark.asyncio
async def test_transaction_exists_requires_all_three_fields(repo: InMemoryCostRepository) -> None:
    """transaction_exists returns False if only date and amount match but description differs."""
    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    result = await repo.transaction_exists(date(2026, 5, 1), Decimal("800.00"), "Andere Beschreibung")

    assert result is False


# ---------------------------------------------------------------------------
# ImportTransactionsUseCase
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_import_transactions_all_new(repo: InMemoryCostRepository) -> None:
    """All rows are new — imported count equals row count, skipped is 0."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("500.00"), "description": "Gehalt", "type": "INCOME"},
        {"date": date(2026, 5, 2), "amount": Decimal("50.00"), "description": "Supermarkt", "type": "EXPENSE"},
    ]
    use_case = ImportTransactionsUseCase(repo)

    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 2
    assert result.skipped == 0
    assert len(repo.transactions) == 2


@pytest.mark.asyncio
async def test_import_transactions_all_duplicates(repo: InMemoryCostRepository) -> None:
    """All rows already exist — imported is 0, skipped equals row count."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("500.00"), "description": "Gehalt", "type": "INCOME"},
    ]
    tx = Transaction.create(
        title="Gehalt",
        amount=Decimal("500.00"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 0
    assert result.skipped == 1
    assert len(repo.transactions) == 1


@pytest.mark.asyncio
async def test_import_transactions_mixed(repo: InMemoryCostRepository) -> None:
    """Mixed rows: some new, some duplicates — counts are accurate."""
    from datetime import date
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    tx = Transaction.create(
        title="Miete",
        amount=Decimal("800.00"),
        transaction_type=TransactionType.EXPENSE,
        transaction_date=date(2026, 5, 1),
    )
    await repo.save_transaction(tx)

    rows = [
        {"date": date(2026, 5, 1), "amount": Decimal("800.00"), "description": "Miete", "type": "EXPENSE"},
        {"date": date(2026, 5, 3), "amount": Decimal("30.00"), "description": "Tankstelle", "type": "EXPENSE"},
    ]
    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=rows, import_source="consorsbank"))

    assert result.imported == 1
    assert result.skipped == 1
    assert len(repo.transactions) == 2


@pytest.mark.asyncio
async def test_import_transactions_empty(repo: InMemoryCostRepository) -> None:
    """Empty rows list — both counts are 0."""
    from src.application.use_cases.cost_use_cases import ImportTransactionsUseCase, ImportTransactionsInput

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(ImportTransactionsInput(parsed_rows=[], import_source="consorsbank"))

    assert result.imported == 0
    assert result.skipped == 0
