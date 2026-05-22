from __future__ import annotations

import logging
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, UploadFile

from src.api.dependencies import CostRepoDep
from src.api.schemas.cost_schemas import (
    CostAnalyticsResponse,
    CostSummaryResponse,
    RecurringCreateRequest,
    RecurringResponse,
    RecurringUpdateRequest,
    TransactionCreateRequest,
    TransactionResponse,
)
from src.application.exceptions import EntityNotFoundError
from src.application.use_cases.cost_use_cases import (
    CreateRecurringUseCase,
    CreateTransactionUseCase,
    DeleteRecurringUseCase,
    DeleteTransactionUseCase,
    EnsureOpeningBalanceTransactionUseCase,
    GenerateMonthlyUseCase,
    GetCostAnalyticsUseCase,
    GetCostSummaryUseCase,
    ListCostTagsUseCase,
    ListRecurringUseCase,
    ListTransactionsUseCase,
    UpdateRecurringUseCase,
)
from src.domain.cost.value_objects import TransactionType

router = APIRouter(prefix="/cost", tags=["cost"])


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@router.post("/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    body: TransactionCreateRequest,
    repo: CostRepoDep,
) -> TransactionResponse:
    transaction = await CreateTransactionUseCase(repo).execute(body.to_use_case_input())
    return TransactionResponse.from_domain(transaction)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    repo: CostRepoDep,
    year: int | None = Query(None, ge=2000, le=2100),
    month: int | None = Query(None, ge=1, le=12),
    tags: list[str] | None = Query(None),
    transaction_type: str | None = Query(None),
) -> list[TransactionResponse]:
    if year is not None and month is not None:
        await EnsureOpeningBalanceTransactionUseCase(repo).execute(year=year, month=month)
    tx_type = TransactionType(transaction_type) if transaction_type else None
    transactions = await ListTransactionsUseCase(repo).execute(
        year=year,
        month=month,
        tags=tags,
        transaction_type=tx_type,
    )
    return [TransactionResponse.from_domain(t) for t in transactions]


@router.delete("/transactions/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: uuid.UUID,
    repo: CostRepoDep,
) -> None:
    await DeleteTransactionUseCase(repo).execute(transaction_id)


# ---------------------------------------------------------------------------
# Recurring
# ---------------------------------------------------------------------------


@router.post("/recurring", response_model=RecurringResponse, status_code=201)
async def create_recurring(
    body: RecurringCreateRequest,
    repo: CostRepoDep,
) -> RecurringResponse:
    recurring = await CreateRecurringUseCase(repo).execute(body.to_use_case_input())
    return RecurringResponse.from_domain(recurring)


@router.get("/recurring", response_model=list[RecurringResponse])
async def list_recurring(
    repo: CostRepoDep,
    active_only: bool = Query(False),
) -> list[RecurringResponse]:
    entries = await ListRecurringUseCase(repo).execute(active_only=active_only)
    return [RecurringResponse.from_domain(r) for r in entries]


@router.patch("/recurring/{recurring_id}", response_model=RecurringResponse)
async def update_recurring(
    recurring_id: uuid.UUID,
    body: RecurringUpdateRequest,
    repo: CostRepoDep,
) -> RecurringResponse:
    recurring = await UpdateRecurringUseCase(repo).execute(body.to_use_case_input(recurring_id))
    return RecurringResponse.from_domain(recurring)


@router.delete("/recurring/{recurring_id}", status_code=204)
async def delete_recurring(
    recurring_id: uuid.UUID,
    repo: CostRepoDep,
) -> None:
    await DeleteRecurringUseCase(repo).execute(recurring_id)


# ---------------------------------------------------------------------------
# Generate Monthly
# ---------------------------------------------------------------------------


@router.post("/generate-monthly", response_model=list[TransactionResponse], status_code=201)
async def generate_monthly(
    repo: CostRepoDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> list[TransactionResponse]:
    created = await GenerateMonthlyUseCase(repo).execute(year=year, month=month)
    return [TransactionResponse.from_domain(t) for t in created]


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    repo: CostRepoDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
) -> CostSummaryResponse:
    await EnsureOpeningBalanceTransactionUseCase(repo).execute(year=year, month=month)
    summary = await GetCostSummaryUseCase(repo).execute(year=year, month=month)
    return CostSummaryResponse(
        year=summary.year,
        month=summary.month,
        income=summary.income,
        expenses=summary.expenses,
        balance=summary.balance,
        transfers=summary.transfers,
        stock_investments=summary.stock_investments,
    )


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.get("/tags", response_model=list[str])
async def list_cost_tags(repo: CostRepoDep) -> list[str]:
    return await ListCostTagsUseCase(repo).execute()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


@router.get("/analytics", response_model=CostAnalyticsResponse)
async def get_cost_analytics(
    repo: CostRepoDep,
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    tags: list[str] | None = Query(None),
) -> CostAnalyticsResponse:
    analytics = await GetCostAnalyticsUseCase(repo).execute(year=year, month=month, tags=tags)
    return CostAnalyticsResponse.from_domain(analytics)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


@router.delete("/reset", status_code=204)
async def reset_all(repo: CostRepoDep) -> None:
    await repo.reset_all()


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

@router.post("/import", response_model=dict)
async def import_csv(file: UploadFile, repo: CostRepoDep) -> dict:
    from src.application.use_cases.cost_use_cases import (
        ImportTransactionsInput,
        ImportTransactionsUseCase,
    )
    from src.config import settings
    from src.infrastructure.import_.csv_parser import (
        CSVParser,
        InvalidCSVFormatError,
        InvalidTransactionDataError,
    )

    filename = (file.filename or "").lower()
    if "consorsbank" in filename:
        import_source = "consorsbank"

        def parse_fn(path: Path) -> list[dict]:
            return CSVParser.parse_consorsbank(path, own_account_ibans=settings.own_account_ibans)

    elif (
        "trade_republic" in filename
        or "traderepublic" in filename
        or "transaktionsexport" in filename
    ):
        import_source = "trade_republic"

        def parse_fn(path: Path) -> list[dict]:
            return CSVParser.parse_trade_republic(path, own_account_ibans=settings.own_account_ibans)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unbekanntes CSV-Format. Dateiname muss 'consorsbank', 'trade_republic' oder 'transaktionsexport' enthalten.",
        )

    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        try:
            parsed_rows = parse_fn(tmp_path)
        except (InvalidCSVFormatError, InvalidTransactionDataError) as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)

    use_case = ImportTransactionsUseCase(repo)
    result = await use_case.execute(
        ImportTransactionsInput(parsed_rows=parsed_rows, import_source=import_source)
    )
    return {"imported": result.imported, "skipped": result.skipped}

