# Phase 10.6 — Saldo-Carryover zwischen Monaten

**Datum:** 2026-05-15  
**Status:** Design-Approved, Implementation-Pending

---

## Overview

Automatische Berechnung und Persistierung von Eröffnungssalden (Opening Balance) für jeden Monat. Der Saldo vom Ende eines Monats wird automatisch als Anfangssaldo-Transaktion für den nächsten Monat erstellt, um kontinuierliche Salden-Rollover zu ermöglichen.

**Scope dieser Phase:**
- Domain: `is_opening_balance` Flag auf Transaction
- Application: Use Cases für Opening Balance Berechnung + Sicherung
- Infrastructure: Alembic Migration
- API: Automatische Erzeugung beim Monat-Load
- Frontend: Anfangssaldo in Transaktionsliste + Summary Cards
- Tests: Unit + Integration Tests

**Out of Scope:**
- Rückdatierung existierender Monate (nur prospektiv)
- Batch-Recalculation von Opening Balances

---

## Architecture

### Backend

#### 1. Domain Extension

**File:** `src/domain/cost/entities.py`

Neues Feld auf `Transaction`:
```python
@dataclass
class Transaction:
    ...
    is_opening_balance: bool = False  # Markiert Anfangssaldo-Transaktionen
```

#### 2. Use Cases

**File:** `src/application/use_cases/cost_use_cases.py`

Zwei neue Use Cases:

**A. `CalculateOpeningBalanceUseCase`**
```python
class CalculateOpeningBalanceUseCase:
    async def execute(self, year: int, month: int) -> Decimal:
        """Calculate opening balance for a month.
        
        Returns: Closing balance of previous month (or 0 if first month)
        """
        # Get previous month transactions
        # Sum: income - expenses
        # Return balance
```

**B. `EnsureOpeningBalanceTransactionUseCase`**
```python
class EnsureOpeningBalanceTransactionUseCase:
    async def execute(self, year: int, month: int) -> Transaction | None:
        """Ensure opening balance transaction exists for month.
        
        - If month is in future → return None (not yet applicable)
        - If month is current month → return None (still open)
        - If month in past:
          - Check if is_opening_balance=true transaction exists
          - If yes → return existing
          - If no → create from previous month's closing balance
        """
```

#### 3. Repository Extension

**File:** `src/domain/cost/repository.py`

Neue Methode auf `ICostRepository`:
```python
async def get_opening_balance_transaction(
    self, year: int, month: int
) -> Transaction | None:
    """Get existing opening balance transaction for month (if any)."""
```

Implementierung in `PostgresCostRepository`:
```python
async def get_opening_balance_transaction(
    self, year: int, month: int
) -> Transaction | None:
    # Query: WHERE is_opening_balance=true AND year=? AND month=?
    # Return first match or None
```

#### 4. Integration in ListTransactionsUseCase

**File:** `src/application/use_cases/cost_use_cases.py`

Modify `ListTransactionsUseCase.execute()`:
```python
async def execute(self, year: int, month: int, ...):
    # NEW: Call EnsureOpeningBalanceUseCase
    ensure_balance_uc = EnsureOpeningBalanceTransactionUseCase(self._repo)
    opening_tx = await ensure_balance_uc.execute(year, month)
    # opening_tx will be created (or None if not applicable)
    
    # Then list all transactions (including opening balance if created)
    return await self._repo.list_transactions(year=year, month=month, ...)
```

#### 5. Infrastructure

**File:** `backend/alembic/versions/*.py`

New migration: Add `is_opening_balance` column to `cost_transactions` table
```sql
ALTER TABLE cost_transactions ADD COLUMN is_opening_balance BOOLEAN DEFAULT FALSE;
CREATE INDEX idx_is_opening_balance ON cost_transactions(is_opening_balance);
```

---

### Frontend

#### 1. TransactionList UI

**File:** `src/features/cost/TransactionList.tsx`

Visual indicator for opening balance transactions:
- Row has muted style (lighter color)
- Badge: "Anfangssaldo" (opening balance label)
- Amount displayed as-is (positive or negative)

#### 2. Summary Cards

**File:** `src/features/cost/SummaryCards.tsx`

Show opening balance separately:
```
┌────────────────────────────────────────────┐
│ Anfangssaldo (April):  +2.000,00 EUR       │
├────────────────────────────────────────────┤
│ Einnahmen (Mai):       +5.000,00 EUR       │
│ Ausgaben (Mai):        −3.000,00 EUR       │
├────────────────────────────────────────────┤
│ Schlusssaldo (Mai):    +4.000,00 EUR       │
└────────────────────────────────────────────┘
```

Calculations:
- `opening_balance` = sum of is_opening_balance=true transactions
- `month_income` = sum of INCOME transactions (excluding opening)
- `month_expenses` = sum of EXPENSE transactions
- `closing_balance` = opening_balance + month_income - month_expenses

#### 3. Hook Update

**File:** `src/api/hooks/cost.ts`

`useTransactions` hook already handles opening balance via auto-generation. No changes needed (it's automatic on list_transactions call).

---

## Data Flow

```
User opens month (e.g., May 2026):

1. Frontend: GET /cost/transactions?year=2026&month=5
2. Backend ListTransactionsUseCase:
   a. Call EnsureOpeningBalanceUseCase.execute(2026, 5)
      - If May in past: Create or fetch opening balance transaction
      - If May current/future: Return None (skip)
   b. Query all transactions for May (including opening balance if created)
3. Frontend renders TransactionList
   - Opening balance row highlighted (muted + badge)
   - Summary Cards show opening + closing balances
```

---

## Validation & Rules

**Opening Balance Creation Rules:**
- Only for **past/current months** (not future)
- **Never** for current month (month open, balance uncertain)
- **Auto-created** on first load of past month (once per month)
- **Immutable** after creation (cannot edit/delete)

**Balance Calculations:**
- Opening Balance = closing balance of previous month
- Month Balance = opening + (income - expenses)
- First month (e.g., January with no December) = opening balance 0

---

## Testing Strategy

**Backend:**

1. **Unit Tests (Domain/Application):**
   - `CalculateOpeningBalanceUseCase` — past month, current month, future month, first month
   - `EnsureOpeningBalanceTransactionUseCase` — creation, idempotency, immutability
   - `ListTransactionsUseCase` — returns opening balance when applicable

2. **Integration Tests (Infrastructure):**
   - Full flow: create April transactions → open May → verify opening balance auto-created
   - Verify opening balance transaction cannot be deleted
   - Verify multiple months have correct carryover

3. **API Tests:**
   - `GET /cost/transactions?year=2026&month=5` includes opening balance for past month
   - Opening balance not present for current month

**Frontend:**

- `TransactionList` renders opening balance row with correct styling
- `SummaryCards` displays opening + closing balances correctly
- `useTransactions` hook integrates opening balance (already works via backend)

---

## Success Criteria

- ✅ Opening balance auto-created for past months on first load
- ✅ Balance rolls over correctly (May opening = April closing)
- ✅ Opening balance immutable (cannot edit/delete)
- ✅ First month (no prior) = opening balance 0€
- ✅ Current month (today): no opening balance created
- ✅ Summary Cards show opening + closing balances
- ✅ TransactionList highlights opening balance row
- ✅ All tests passing (backend + frontend)
- ✅ No regressions in existing cost features

