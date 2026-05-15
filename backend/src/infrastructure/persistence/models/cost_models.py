from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class TransactionModel(Base):
    __tablename__ = "cost_transactions"
    __table_args__ = (
        Index("ix_cost_transactions_date", "date"),
        Index("ix_cost_transactions_type", "transaction_type"),
        Index("ix_cost_transactions_recurring_source_id", "recurring_source_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[object] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recurring_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cost_recurring.id", ondelete="SET NULL"),
        nullable=True,
    )
    import_source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_opening_balance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class RecurringTransactionModel(Base):
    __tablename__ = "cost_recurring"
    __table_args__ = (
        Index("ix_cost_recurring_is_active", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[object] = mapped_column(Numeric(precision=12, scale=2), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    interval: Mapped[str] = mapped_column(String(10), nullable=False)
    day_of_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
