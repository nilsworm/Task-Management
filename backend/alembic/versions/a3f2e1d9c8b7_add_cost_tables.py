"""add cost tables

Revision ID: a3f2e1d9c8b7
Revises: 10acb523279a
Create Date: 2026-04-29 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a3f2e1d9c8b7"
down_revision = "7013b7d457bf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # cost_recurring must be created first (FK target)
    op.create_table(
        "cost_recurring",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("interval", sa.String(10), nullable=False),
        sa.Column("day_of_month", sa.Integer(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cost_recurring_is_active", "cost_recurring", ["is_active"])

    op.create_table(
        "cost_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("transaction_type", sa.String(10), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("recurring_source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["recurring_source_id"],
            ["cost_recurring.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cost_transactions_date", "cost_transactions", ["date"])
    op.create_index(
        "ix_cost_transactions_type", "cost_transactions", ["transaction_type"]
    )
    op.create_index(
        "ix_cost_transactions_recurring_source_id",
        "cost_transactions",
        ["recurring_source_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_cost_transactions_recurring_source_id", "cost_transactions")
    op.drop_index("ix_cost_transactions_type", "cost_transactions")
    op.drop_index("ix_cost_transactions_date", "cost_transactions")
    op.drop_table("cost_transactions")

    op.drop_index("ix_cost_recurring_is_active", "cost_recurring")
    op.drop_table("cost_recurring")
