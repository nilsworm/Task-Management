# Trade Republic CSV Import + Transfer/Stock Types

**Date:** 2026-05-22
**Branch:** feature/trade-republic-import

---

## Problem

`parse_trade_republic` was written for a now-defunct PDF-converted format (`Datum, Beschreibung, Typ, Betrag`). The real Trade Republic export (`Transaktionsexport.csv`) has a completely different schema. Additionally, inter-account transfers between Consorsbank and Trade Republic currently create false income/expense entries on both sides.

---

## New Transaction Types

Two new values added to `TransactionType`:

| Type | Meaning | Affects balance? | Shown in overview/analytics? |
|---|---|---|---|
| `TRANSFER` | Inter-account transfer between own accounts | No | Yes |
| `STOCK` | ETF/stock purchase at Trade Republic | No | Yes |

Summary and analytics treat TRANSFER and STOCK as separate categories — they appear but do not count toward income, expenses, or balance.

---

## Configuration

New env variable in `config.py`:

```
OWN_ACCOUNT_IBANS=DE80760300800270566776,DE44100123450409695601
```

- `DE80760300800270566776` — user's Consorsbank account (ends in 776)
- `DE44100123450409695601` — user's Trade Republic account (BIC: TRBKDEBBXXX)

`Settings.own_account_ibans: list[str] = []` — parsed from comma-separated string.

---

## Parser Changes

### Consorsbank (`parse_consorsbank`)

Additional parameter: `own_account_ibans: list[str] = []`

**New rule:** If `IBAN` column value is in `own_account_ibans` → emit row with `type = "TRANSFER"` instead of skipping.

Everything else unchanged.

### Trade Republic (`parse_trade_republic`) — full rewrite

Real CSV columns: `datetime, date, account_type, category, type, asset_class, name, symbol, shares, price, amount, fee, tax, currency, ...counterparty_iban...`

Additional parameter: `own_account_ibans: list[str] = []`

**Type mapping:**

| TR `type` | Condition | Action |
|---|---|---|
| `TRANSFER_INBOUND` | `counterparty_iban` in `own_account_ibans` | Skip |
| `TRANSFER_INBOUND` | `counterparty_iban` not in own accounts | `INCOME` |
| `BUY` | — | `STOCK` |
| `FREE_RECEIPT` | — | Skip (no cash amount) |
| `CUSTOMER_INPAYMENT` | — | Skip (own-account direct debit top-up) |
| `CARD_TRANSACTION` | — | `EXPENSE` |
| `INTEREST_PAYMENT` | — | `INCOME` |
| `DIVIDEND` | — | `INCOME` |
| `BENEFITS_SAVEBACK` | — | `INCOME` |

**Description:** `name` field if non-empty, otherwise TR `type` value as fallback.

**Amount:** `amount` column (dot-decimal, 6 decimal places). Sign determines INCOME/EXPENSE; absolute value stored.

**Filename detection:** Add `"transaktionsexport"` to TR format detection in `cost_router.py`.

---

## Summary (`GetCostSummaryUseCase`)

Current response: `income`, `expenses`, `balance`.

Extended response adds:
- `transfers: Decimal` — sum of TRANSFER transactions
- `stock_investments: Decimal` — sum of STOCK transactions

`balance = income - expenses` (unchanged — TRANSFER and STOCK do not affect it).

---

## Analytics (`GetCostAnalyticsUseCase`)

TRANSFER and STOCK transactions appear as named categories in the existing breakdown. No structural change to the analytics query needed — they group naturally by type/tag.

---

## Infrastructure

### `TransactionType` enum
Add `TRANSFER = "TRANSFER"` and `STOCK = "STOCK"`.

### Alembic migration
Extend the `transactiontype` PostgreSQL enum with the two new values.

### `ImportTransactionsUseCase`
Reads `settings.own_account_ibans` and passes it to both parsers.

---

## Tests

- `TestCSVParserConsorsbank`: add test for TR-IBAN row → `TRANSFER` type
- `TestCSVParserTradeRepublic`: replace 3 existing tests with tests for real TR CSV format:
  - Cash transactions (CARD → EXPENSE, INTEREST/DIVIDEND/SAVEBACK → INCOME)
  - Investment transactions (BUY → STOCK)
  - Skip rows (TRANSFER_INBOUND with own IBAN, FREE_RECEIPT, CUSTOMER_INPAYMENT)
  - Missing columns → `InvalidCSVFormatError`
  - Invalid amount → `InvalidTransactionDataError`
- `TestGetCostSummaryUseCase`: verify `transfers` and `stock_investments` fields
- API tests for `POST /cost/import` with `transaktionsexport` filename
