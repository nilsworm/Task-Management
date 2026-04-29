from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from src.api.dependencies import CostRepoDep
from src.api.schemas.cost_schemas import (
    RecurringCreateRequest,
    RecurringResponse,
    TransactionCreateRequest,
    TransactionResponse,
)
from src.application.exceptions import EntityNotFoundError
from src.application.use_cases.cost_use_cases import (
    CreateRecurringUseCase,
    CreateTransactionUseCase,
    DeleteRecurringUseCase,
    DeleteTransactionUseCase,
    ListCostTagsUseCase,
    ListRecurringUseCase,
    ListTransactionsUseCase,
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


@router.delete("/recurring/{recurring_id}", status_code=204)
async def delete_recurring(
    recurring_id: uuid.UUID,
    repo: CostRepoDep,
) -> None:
    await DeleteRecurringUseCase(repo).execute(recurring_id)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@router.get("/tags", response_model=list[str])
async def list_cost_tags(repo: CostRepoDep) -> list[str]:
    return await ListCostTagsUseCase(repo).execute()
