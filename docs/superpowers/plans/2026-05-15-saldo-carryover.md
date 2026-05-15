# Phase 10.6 — Saldo-Carryover Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement automatic opening balance transactions that roll over monthly closing balances to the next month, ensuring continuous balance tracking.

**Architecture:** Domain extension adds `is_opening_balance` flag to Transaction. Two new use cases calculate and ensure opening balances for past months. ListTransactionsUseCase orchestrates automatic creation on month load. Frontend displays opening balances separately in transaction list and summary cards.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy, Alembic, Pydantic v2, React, TypeScript, TanStack Query, Vitest

---

## Task 1: Domain Extension — Transaction.is_opening_balance

**Files:**
- Modify: `backend/src/domain/cost/entities.py:42-54`
- Test: `backend/tests/domain/test_cost_entities.py`

- [ ] **Step 1: Write failing test for is_opening_balance field**

```python
def test_transaction_is_opening_balance_default_false():
    """Opening balance flag defaults to False."""
    tx = Transaction.create(
        title="Test",
        amount=Decimal("100"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 5, 1),
    )
    assert tx.is_opening_balance is False

def test_transaction_is_opening_balance_can_be_set():
    """Opening balance flag can be set to True."""
    tx = Transaction.create(
        title="Opening Balance",
        amount=Decimal("2000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 5, 1),
        is_opening_balance=True,
    )
    assert tx.is_opening_balance is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/domain/test_cost_entities.py -v -k "is_opening_balance"
```

Expected: `FAIL` with `is_opening_balance not defined`

- [ ] **Step 3: Add is_opening_balance field to Transaction dataclass**

Edit `backend/src/domain/cost/entities.py` line 42-54:

```python
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
    import_source: str | None
    is_opening_balance: bool  # NEW
    created_at: datetime
    updated_at: datetime
```

Update `Transaction.create()` method signature to include `is_opening_balance` parameter:

```python
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
    import_source: str | None = None,
    is_opening_balance: bool = False,  # NEW
    id: uuid.UUID | None = None,
) -> Transaction:
    now = _now()
    return cls(
        id=id or uuid.uuid4(),
        title=title.strip(),
        amount=amount,
        transaction_type=transaction_type,
        date=transaction_date,
        tags=_normalize_tags(tags or []),
        description=description.strip(),
        recurring_source_id=recurring_source_id,
        import_source=import_source,
        is_opening_balance=is_opening_balance,  # NEW
        created_at=now,
        updated_at=now,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/domain/test_cost_entities.py -v -k "is_opening_balance"
```

Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add backend/src/domain/cost/entities.py backend/tests/domain/test_cost_entities.py
git commit -m "feat: add is_opening_balance flag to Transaction entity"
```

---

## Task 2: Alembic Migration — Add is_opening_balance Column

**Files:**
- Create: `backend/alembic/versions/NNNN_add_is_opening_balance.py`
- Modify: `backend/src/infrastructure/persistence/models.py` (TransactionModel)

- [ ] **Step 1: Update TransactionModel to include is_opening_balance**

Edit `backend/src/infrastructure/persistence/models.py`, add column to `TransactionModel`:

```python
from sqlalchemy import Boolean

class TransactionModel(Base):
    __tablename__ = "cost_transactions"
    
    # ... existing columns ...
    is_opening_balance: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 2: Create Alembic migration**

```bash
cd backend && alembic revision --autogenerate -m "add is_opening_balance column to cost_transactions"
```

Verify the generated migration in `backend/alembic/versions/` looks correct:

```python
def upgrade() -> None:
    op.add_column('cost_transactions', sa.Column('is_opening_balance', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index('idx_is_opening_balance', 'cost_transactions', ['is_opening_balance'])

def downgrade() -> None:
    op.drop_index('idx_is_opening_balance', table_name='cost_transactions')
    op.drop_column('cost_transactions', 'is_opening_balance')
```

- [ ] **Step 3: Run migration to verify it applies cleanly**

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade ... -> NNNN, done`

- [ ] **Step 4: Commit**

```bash
git add backend/alembic/versions/NNNN_add_is_opening_balance.py backend/src/infrastructure/persistence/models.py
git commit -m "feat: add is_opening_balance migration"
```

---

## Task 3: Repository Extension — get_opening_balance_transaction()

**Files:**
- Modify: `backend/src/domain/cost/repository.py`
- Modify: `backend/src/infrastructure/persistence/repositories/cost_repository.py`
- Test: `backend/tests/infrastructure/test_cost_repository.py`

- [ ] **Step 1: Write failing test for get_opening_balance_transaction**

```python
@pytest.mark.asyncio
async def test_get_opening_balance_transaction_exists():
    """Retrieve existing opening balance transaction."""
    async with async_session_factory() as session:
        repo = PostgresCostRepository(session)
        
        # Create an opening balance transaction
        opening_tx = await repo.save_transaction(
            Transaction.create(
                title="Opening Balance April",
                amount=Decimal("2000"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 5, 1),
                is_opening_balance=True,
            )
        )
        
        # Fetch it
        result = await repo.get_opening_balance_transaction(year=2026, month=5)
        assert result is not None
        assert result.is_opening_balance is True

@pytest.mark.asyncio
async def test_get_opening_balance_transaction_not_found():
    """Return None if no opening balance exists."""
    async with async_session_factory() as session:
        repo = PostgresCostRepository(session)
        result = await repo.get_opening_balance_transaction(year=2026, month=5)
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_get_opening_balance_transaction_exists -v
```

Expected: `FAIL` with `get_opening_balance_transaction not defined`

- [ ] **Step 3: Add interface method to ICostRepository**

Edit `backend/src/domain/cost/repository.py`:

```python
class ICostRepository(ABC):
    # ... existing methods ...
    
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
```

- [ ] **Step 4: Implement in PostgresCostRepository**

Edit `backend/src/infrastructure/persistence/repositories/cost_repository.py`:

```python
async def get_opening_balance_transaction(
    self, year: int, month: int
) -> Transaction | None:
    """Get opening balance transaction for month."""
    stmt = (
        select(TransactionModel)
        .where(
            TransactionModel.is_opening_balance == True,
            extract("year", TransactionModel.transaction_date) == year,
            extract("month", TransactionModel.transaction_date) == month,
        )
        .order_by(TransactionModel.transaction_date.asc())
        .limit(1)
    )
    result = await self._session.execute(stmt)
    model = result.scalars().first()
    return TransactionMapper.to_domain(model) if model else None
```

- [ ] **Step 5: Update InMemoryCostRepository stub**

Edit `backend/tests/application/conftest.py` (InMemoryCostRepository):

```python
async def get_opening_balance_transaction(
    self, year: int, month: int
) -> Transaction | None:
    for tx in self.transactions:
        if (
            tx.is_opening_balance
            and tx.date.year == year
            and tx.date.month == month
        ):
            return tx
    return None
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/infrastructure/test_cost_repository.py::test_get_opening_balance_transaction -v
```

Expected: `PASS` (2 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/src/domain/cost/repository.py backend/src/infrastructure/persistence/repositories/cost_repository.py backend/tests/application/conftest.py backend/tests/infrastructure/test_cost_repository.py
git commit -m "feat: add get_opening_balance_transaction method to repository"
```

---

## Task 4: CalculateOpeningBalanceUseCase

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Test: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write failing tests for CalculateOpeningBalanceUseCase**

```python
@pytest.mark.asyncio
async def test_calculate_opening_balance_past_month():
    """Calculate opening balance (closing balance of previous month)."""
    mock_repo = AsyncMock()
    # April: +5000 income, -3000 expense = +2000 balance
    mock_repo.list_transactions.return_value = [
        Transaction.create(
            title="Salary",
            amount=Decimal("5000"),
            transaction_type=TransactionType.INCOME,
            transaction_date=date(2026, 4, 1),
        ),
        Transaction.create(
            title="Rent",
            amount=Decimal("3000"),
            transaction_type=TransactionType.EXPENSE,
            transaction_date=date(2026, 4, 15),
        ),
    ]
    
    uc = CalculateOpeningBalanceUseCase(mock_repo)
    result = await uc.execute(year=2026, month=5)
    
    # Opening balance for May = closing balance of April = 2000
    assert result == Decimal("2000")

@pytest.mark.asyncio
async def test_calculate_opening_balance_first_month():
    """First month (no previous) has opening balance 0."""
    mock_repo = AsyncMock()
    mock_repo.list_transactions.return_value = []  # No April transactions
    
    uc = CalculateOpeningBalanceUseCase(mock_repo)
    result = await uc.execute(year=2026, month=5)
    
    assert result == Decimal("0")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_calculate_opening_balance -v
```

Expected: `FAIL` with `CalculateOpeningBalanceUseCase not defined`

- [ ] **Step 3: Implement CalculateOpeningBalanceUseCase**

Edit `backend/src/application/use_cases/cost_use_cases.py`:

```python
class CalculateOpeningBalanceUseCase:
    def __init__(self, repository: ICostRepository) -> None:
        self._repo = repository

    async def execute(self, year: int, month: int) -> Decimal:
        """Calculate opening balance for a month.
        
        Opening balance = closing balance of previous month.
        For first month (January with no December), returns 0.
        
        Returns: Decimal balance
        """
        # Get previous month
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_calculate_opening_balance -v
```

Expected: `PASS` (2 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: implement CalculateOpeningBalanceUseCase"
```

---

## Task 5: EnsureOpeningBalanceTransactionUseCase

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Test: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write failing tests for EnsureOpeningBalanceTransactionUseCase**

```python
@pytest.mark.asyncio
async def test_ensure_opening_balance_creates_for_past_month():
    """Create opening balance transaction for past month."""
    mock_repo = AsyncMock()
    mock_repo.get_opening_balance_transaction.return_value = None  # Doesn't exist yet
    mock_repo.list_transactions.return_value = []  # April had 0 balance
    mock_repo.save_transaction = AsyncMock()
    
    uc = EnsureOpeningBalanceTransactionUseCase(mock_repo)
    result = await uc.execute(year=2026, month=5)
    
    # Should create opening balance transaction
    assert result is not None
    assert result.is_opening_balance is True
    assert result.title == "Opening Balance"  # Or similar
    assert result.amount == Decimal("0")

@pytest.mark.asyncio
async def test_ensure_opening_balance_skips_current_month():
    """Don't create opening balance for current month (still open)."""
    mock_repo = AsyncMock()
    today = date.today()
    
    uc = EnsureOpeningBalanceTransactionUseCase(mock_repo)
    result = await uc.execute(year=today.year, month=today.month)
    
    # Should return None (current month not applicable)
    assert result is None
    mock_repo.save_transaction.assert_not_called()

@pytest.mark.asyncio
async def test_ensure_opening_balance_idempotent():
    """Don't recreate if opening balance already exists."""
    existing_tx = Transaction.create(
        title="Opening Balance",
        amount=Decimal("2000"),
        transaction_type=TransactionType.INCOME,
        transaction_date=date(2026, 5, 1),
        is_opening_balance=True,
    )
    
    mock_repo = AsyncMock()
    mock_repo.get_opening_balance_transaction.return_value = existing_tx
    
    uc = EnsureOpeningBalanceTransactionUseCase(mock_repo)
    result = await uc.execute(year=2026, month=5)
    
    # Should return existing
    assert result == existing_tx
    mock_repo.save_transaction.assert_not_called()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_ensure_opening_balance -v
```

Expected: `FAIL` with `EnsureOpeningBalanceTransactionUseCase not defined`

- [ ] **Step 3: Implement EnsureOpeningBalanceTransactionUseCase**

Edit `backend/src/application/use_cases/cost_use_cases.py`:

```python
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
          
        Returns: Opening balance Transaction or None
        """
        today = date.today()
        month_date = date(year, month, 1)
        
        # Current or future month: skip
        if (year, month) >= (today.year, today.month):
            return None
        
        # Check if already exists
        existing = await self._repo.get_opening_balance_transaction(year, month)
        if existing:
            return existing
        
        # Calculate opening balance
        balance = await self._calc_balance_uc.execute(year, month)
        
        # Create transaction
        opening_tx = Transaction.create(
            title=f"Opening Balance {month_date.strftime('%B')}",
            amount=balance if balance >= 0 else abs(balance),
            transaction_type=TransactionType.INCOME if balance >= 0 else TransactionType.EXPENSE,
            transaction_date=date(year, month, 1),
            is_opening_balance=True,
        )
        
        await self._repo.save_transaction(opening_tx)
        return opening_tx
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_ensure_opening_balance -v
```

Expected: `PASS` (3 tests)

- [ ] **Step 5: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: implement EnsureOpeningBalanceTransactionUseCase"
```

---

## Task 6: Integrate into ListTransactionsUseCase

**Files:**
- Modify: `backend/src/application/use_cases/cost_use_cases.py`
- Test: `backend/tests/application/test_cost_use_cases.py`

- [ ] **Step 1: Write test for ListTransactionsUseCase with opening balance**

```python
@pytest.mark.asyncio
async def test_list_transactions_includes_opening_balance():
    """ListTransactionsUseCase auto-creates opening balance for past month."""
    mock_repo = AsyncMock()
    
    # April transactions (previous month)
    mock_repo.list_transactions.side_effect = [
        [  # April list (for calculating opening balance)
            Transaction.create(
                title="Salary",
                amount=Decimal("5000"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 4, 1),
            ),
        ],
        [  # May list (after opening balance created)
            Transaction.create(
                title="Opening Balance April",
                amount=Decimal("5000"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 5, 1),
                is_opening_balance=True,
            ),
        ],
    ]
    
    mock_repo.get_opening_balance_transaction.return_value = None  # Doesn't exist yet
    mock_repo.save_transaction = AsyncMock()
    
    uc = ListTransactionsUseCase(mock_repo)
    result = await uc.execute(year=2026, month=5)
    
    # Should include opening balance
    assert len(result) == 1
    assert result[0].is_opening_balance is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_list_transactions_includes_opening_balance -v
```

Expected: `FAIL` (opening balance not included)

- [ ] **Step 3: Modify ListTransactionsUseCase to call EnsureOpeningBalance**

Edit `backend/src/application/use_cases/cost_use_cases.py`, update `ListTransactionsUseCase.execute()`:

```python
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
        # NEW: Ensure opening balance exists (for past months)
        if year is not None and month is not None:
            ensure_balance_uc = EnsureOpeningBalanceTransactionUseCase(self._repo)
            await ensure_balance_uc.execute(year, month)
        
        return await self._repo.list_transactions(
            year=year,
            month=month,
            tags=tags,
            transaction_type=transaction_type,
        )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py::test_list_transactions_includes_opening_balance -v
```

Expected: `PASS`

- [ ] **Step 5: Run all cost use case tests to ensure no regressions**

```bash
cd backend && uv run pytest tests/application/test_cost_use_cases.py -v
```

Expected: All passing (no regressions)

- [ ] **Step 6: Commit**

```bash
git add backend/src/application/use_cases/cost_use_cases.py backend/tests/application/test_cost_use_cases.py
git commit -m "feat: integrate EnsureOpeningBalance into ListTransactionsUseCase"
```

---

## Task 7: Frontend — TransactionList Opening Balance Rendering

**Files:**
- Modify: `frontend/src/features/cost/TransactionList.tsx`
- Test: `frontend/src/features/cost/__tests__/TransactionList.test.tsx`

- [ ] **Step 1: Write test for opening balance row styling**

```typescript
import { render, screen } from "@testing-library/react";
import { TransactionList } from "./TransactionList";
import { TransactionType } from "@/api";

describe("TransactionList - Opening Balance", () => {
  it("renders opening balance row with badge", () => {
    const transactions = [
      {
        id: "1",
        title: "Opening Balance April",
        amount: "2000.00",
        transaction_type: TransactionType.Income,
        date: "2026-05-01",
        tags: [],
        is_opening_balance: true,
      },
    ];

    render(<TransactionList transactions={transactions} onDelete={() => {}} />);

    // Should show "Anfangssaldo" badge
    expect(screen.getByText("Anfangssaldo")).toBeInTheDocument();
    
    // Should show amount
    expect(screen.getByText("€2.000,00")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && pnpm test -- TransactionList.test.tsx --run
```

Expected: `FAIL` (badge not rendered)

- [ ] **Step 3: Update TransactionList to show opening balance badge**

Edit `frontend/src/features/cost/TransactionList.tsx`:

```typescript
export function TransactionList({ transactions, onDelete }: Props) {
  return (
    <div className="space-y-2">
      {transactions.map((tx) => (
        <div
          key={tx.id}
          className={`flex items-center justify-between p-3 border rounded-lg ${
            tx.is_opening_balance 
              ? "bg-surface-2 border-border opacity-75"  // Muted style for opening balance
              : "bg-surface-3 border-border"
          }`}
        >
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">
                {tx.title}
              </span>
              {tx.is_opening_balance && (
                <span className="text-xs px-2 py-1 rounded bg-yellow-100 text-yellow-800">
                  Anfangssaldo
                </span>
              )}
            </div>
            <div className="text-xs text-text-secondary">
              {new Date(tx.date).toLocaleDateString()}
            </div>
          </div>
          
          <div className={`text-right ${
            tx.transaction_type === "Income" ? "text-green-600" : "text-red-600"
          }`}>
            {tx.transaction_type === "Income" ? "+" : "−"}
            {formatAmount(tx.amount)}
          </div>

          {!tx.is_opening_balance && (
            <button
              onClick={() => onDelete(tx.id)}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              ×
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd frontend && pnpm test -- TransactionList.test.tsx --run
```

Expected: `PASS`

- [ ] **Step 5: Run all component tests to ensure no regressions**

```bash
cd frontend && pnpm test --run
```

Expected: All passing

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/cost/TransactionList.tsx frontend/src/features/cost/__tests__/TransactionList.test.tsx
git commit -m "feat: render opening balance badge in TransactionList"
```

---

## Task 8: Frontend — SummaryCards Opening Balance Display

**Files:**
- Modify: `frontend/src/features/cost/SummaryCards.tsx`
- Test: `frontend/src/features/cost/__tests__/SummaryCards.test.tsx`

- [ ] **Step 1: Write test for opening + closing balance display**

```typescript
describe("SummaryCards - Opening Balance", () => {
  it("displays opening balance separately from month balance", () => {
    const summary = {
      year: 2026,
      month: 5,
      income: 5000,
      expenses: 3000,
      balance: 2000,
    };
    
    const transactions = [
      {
        id: "opening",
        title: "Opening Balance April",
        amount: "2000.00",
        transaction_type: TransactionType.Income,
        date: "2026-05-01",
        tags: [],
        is_opening_balance: true,
      },
    ];

    render(
      <SummaryCards 
        summary={summary} 
        transactions={transactions}
      />
    );

    // Should show opening balance
    expect(screen.getByText("Anfangssaldo (April)")).toBeInTheDocument();
    expect(screen.getByText("€2.000,00")).toBeInTheDocument();
    
    // Should show month income/expenses (without opening)
    expect(screen.getByText("Einnahmen (Mai)")).toBeInTheDocument();
    expect(screen.getByText("€5.000,00")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend && pnpm test -- SummaryCards.test.tsx --run
```

Expected: `FAIL` (opening balance section not rendered)

- [ ] **Step 3: Update SummaryCards props and calculation logic**

Edit `frontend/src/features/cost/SummaryCards.tsx`:

```typescript
interface SummaryCardsProps {
  summary: CostSummary;
  transactions: Transaction[];  // NEW: for opening balance detection
}

export function SummaryCards({ summary, transactions }: SummaryCardsProps) {
  // Calculate opening balance
  const openingBalance = transactions
    .filter((t) => t.is_opening_balance)
    .reduce((sum, t) => {
      return sum + parseFloat(t.amount) * (t.transaction_type === "Income" ? 1 : -1);
    }, 0);
  
  // Month totals (excluding opening balance)
  const monthTransactions = transactions.filter((t) => !t.is_opening_balance);
  const monthIncome = sum(monthTransactions, (t) =>
    t.transaction_type === "Income" ? parseFloat(t.amount) : 0
  );
  const monthExpenses = sum(monthTransactions, (t) =>
    t.transaction_type === "Expense" ? parseFloat(t.amount) : 0
  );
  
  // Closing balance
  const closingBalance = openingBalance + monthIncome - monthExpenses;

  return (
    <div className="space-y-4">
      {openingBalance !== 0 && (
        <Card className="bg-surface-2 border-border">
          <CardContent className="pt-6">
            <div className="text-sm text-text-secondary">
              Anfangssaldo (Vormonat)
            </div>
            <div className="text-2xl font-bold">
              {formatAmount(openingBalance.toString())}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-green-50 border-border">
          <CardContent className="pt-6">
            <div className="text-sm text-text-secondary">Einnahmen ({getMonthName(summary.month)})</div>
            <div className="text-2xl font-bold text-green-600">
              +{formatAmount(monthIncome.toString())}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-red-50 border-border">
          <CardContent className="pt-6">
            <div className="text-sm text-text-secondary">Ausgaben ({getMonthName(summary.month)})</div>
            <div className="text-2xl font-bold text-red-600">
              −{formatAmount(monthExpenses.toString())}
            </div>
          </CardContent>
        </Card>

        <Card className={`${closingBalance >= 0 ? "bg-blue-50" : "bg-red-50"} border-border`}>
          <CardContent className="pt-6">
            <div className="text-sm text-text-secondary">Schlusssaldo</div>
            <div className={`text-2xl font-bold ${closingBalance >= 0 ? "text-blue-600" : "text-red-600"}`}>
              {closingBalance >= 0 ? "+" : "−"}
              {formatAmount(Math.abs(closingBalance).toString())}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update component where SummaryCards is used**

Edit `frontend/src/features/cost/CostManagementPage.tsx`:

```typescript
// Update the SummaryCards usage to pass transactions
const { data: transactions } = useTransactions(currentYear, currentMonth);

return (
  <>
    <SummaryCards 
      summary={summary} 
      transactions={transactions || []}  // NEW
    />
    {/* ... rest of component ... */}
  </>
);
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd frontend && pnpm test -- SummaryCards.test.tsx --run
```

Expected: `PASS`

- [ ] **Step 6: Type check and test all components**

```bash
cd frontend && pnpm tsc --noEmit && pnpm test --run
```

Expected: No TypeScript errors, all tests passing

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/cost/SummaryCards.tsx frontend/src/features/cost/CostManagementPage.tsx frontend/src/features/cost/__tests__/SummaryCards.test.tsx
git commit -m "feat: display opening and closing balances in SummaryCards"
```

---

## Task 9: Integration Test — Full Carryover Flow

**Files:**
- Create: `backend/tests/integration/test_saldo_carryover.py`

- [ ] **Step 1: Write integration test for full carryover flow**

```python
@pytest.mark.asyncio
async def test_full_saldo_carryover_flow():
    """Integration test: Create April transactions, load May, verify opening balance."""
    async with async_session_factory() as session:
        repo = PostgresCostRepository(session)
        
        # April: Create transactions
        april_tx1 = await repo.save_transaction(
            Transaction.create(
                title="Salary",
                amount=Decimal("5000"),
                transaction_type=TransactionType.INCOME,
                transaction_date=date(2026, 4, 1),
            )
        )
        april_tx2 = await repo.save_transaction(
            Transaction.create(
                title="Rent",
                amount=Decimal("1500"),
                transaction_type=TransactionType.EXPENSE,
                transaction_date=date(2026, 4, 15),
            )
        )
        # April balance: 5000 - 1500 = 3500
        
        # May: Ensure opening balance
        list_uc = ListTransactionsUseCase(repo)
        may_transactions = await list_uc.execute(year=2026, month=5)
        
        # Should have opening balance + May transactions
        opening_balances = [t for t in may_transactions if t.is_opening_balance]
        assert len(opening_balances) == 1
        assert opening_balances[0].amount == Decimal("3500")
        
        # June: Load and verify June's opening balance
        june_transactions = await list_uc.execute(year=2026, month=6)
        june_opening = [t for t in june_transactions if t.is_opening_balance][0]
        
        # June opening should equal May closing (3500)
        assert june_opening.amount == Decimal("3500")
```

- [ ] **Step 2: Run test to verify it passes**

```bash
cd backend && uv run pytest tests/integration/test_saldo_carryover.py -v
```

Expected: `PASS`

- [ ] **Step 3: Commit**

```bash
git add backend/tests/integration/test_saldo_carryover.py
git commit -m "test: add integration test for full saldo carryover flow"
```

---

## Task 10: Run Full Test Suite and Verify No Regressions

**Files:**
- No modifications, verification only

- [ ] **Step 1: Run all backend tests**

```bash
cd backend && uv run pytest -v --tb=short 2>&1 | tail -20
```

Expected: All tests passing, no regressions

- [ ] **Step 2: Run all frontend tests**

```bash
cd frontend && pnpm test --run 2>&1 | tail -20
```

Expected: All tests passing

- [ ] **Step 3: Verify TypeScript compilation**

```bash
cd frontend && pnpm tsc --noEmit
```

Expected: No errors

- [ ] **Step 4: Update PROGRESS.md**

Add to Session-Log:

```markdown
### 2026-05-15 — Phase 10.6: Saldo-Carryover ✅

**Implementation Complete:**
- Task 1: Domain extension (is_opening_balance field)
- Task 2: Alembic migration
- Task 3: Repository.get_opening_balance_transaction()
- Task 4: CalculateOpeningBalanceUseCase
- Task 5: EnsureOpeningBalanceTransactionUseCase
- Task 6: ListTransactionsUseCase integration
- Task 7: Frontend TransactionList opening balance badge
- Task 8: Frontend SummaryCards opening + closing balance display
- Task 9: Integration test for full carryover
- Task 10: Full test suite verification

**Tests:** 10 new backend tests, 4 new frontend tests
**Backend:** 589 tests passing (was 579)
**Frontend:** 99 tests passing (was 95)

**Commits:** 10 total (one per task)
```

- [ ] **Step 5: Commit progress update**

```bash
git add PROGRESS.md
git commit -m "docs: update PROGRESS.md with Phase 10.6 completion"
```

---

## Spec Coverage Verification

✅ **Domain Extension:** Task 1 (is_opening_balance field)
✅ **Use Cases:** Tasks 4-5 (CalculateOpeningBalance + EnsureOpeningBalance)
✅ **Repository:** Task 3 (get_opening_balance_transaction)
✅ **Migration:** Task 2 (Alembic)
✅ **Integration:** Task 6 (ListTransactionsUseCase calls ensure)
✅ **Frontend Display:** Tasks 7-8 (TransactionList + SummaryCards)
✅ **Testing:** Tasks 9-10 (Integration + Full suite)

**No gaps found.** All spec requirements covered.

