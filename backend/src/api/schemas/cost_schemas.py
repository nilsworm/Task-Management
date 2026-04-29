from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src.application.use_cases.cost_use_cases import CreateRecurringInput, CreateTransactionInput
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType


def _validated_tags(tags: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        normalized = tag.strip().lower()
        if not normalized:
            raise ValueError("tag cannot be empty")
        if len(normalized) > 50:
            raise ValueError("tag cannot exceed 50 characters")
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


class TransactionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    transaction_type: Literal["income", "expense"]
    date: date
    tags: list[str] = Field(default_factory=list, max_length=20)
    description: str = Field(default="", max_length=1000)

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        return _validated_tags(v)

    def to_use_case_input(self) -> CreateTransactionInput:
        return CreateTransactionInput(
            title=self.title,
            amount=self.amount,
            transaction_type=TransactionType(self.transaction_type),
            date=self.date,
            tags=self.tags,
            description=self.description,
        )


class TransactionResponse(BaseModel):
    id: uuid.UUID
    title: str
    amount: Decimal
    transaction_type: str
    date: date
    tags: list[str]
    description: str
    recurring_source_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_domain(cls, t: Transaction) -> TransactionResponse:
        return cls(
            id=t.id,
            title=t.title,
            amount=t.amount,
            transaction_type=t.transaction_type.value,
            date=t.date,
            tags=t.tags,
            description=t.description,
            recurring_source_id=t.recurring_source_id,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )


class RecurringCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=12, decimal_places=2)
    transaction_type: Literal["income", "expense"]
    interval: Literal["weekly", "monthly", "yearly"]
    day_of_month: int | None = Field(None, ge=1, le=28)
    tags: list[str] = Field(default_factory=list, max_length=20)
    start_date: date | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        return _validated_tags(v)

    def to_use_case_input(self) -> CreateRecurringInput:
        return CreateRecurringInput(
            title=self.title,
            amount=self.amount,
            transaction_type=TransactionType(self.transaction_type),
            interval=RecurrenceInterval(self.interval),
            day_of_month=self.day_of_month,
            tags=self.tags,
            start_date=self.start_date,
        )


class RecurringResponse(BaseModel):
    id: uuid.UUID
    title: str
    amount: Decimal
    transaction_type: str
    interval: str
    day_of_month: int | None
    tags: list[str]
    is_active: bool
    start_date: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_domain(cls, r: RecurringTransaction) -> RecurringResponse:
        return cls(
            id=r.id,
            title=r.title,
            amount=r.amount,
            transaction_type=r.transaction_type.value,
            interval=r.interval.value,
            day_of_month=r.day_of_month,
            tags=r.tags,
            is_active=r.is_active,
            start_date=r.start_date,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
