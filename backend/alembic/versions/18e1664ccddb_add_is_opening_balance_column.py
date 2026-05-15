"""add is_opening_balance column to cost_transactions

Revision ID: 18e1664ccddb
Revises: 71c1c1969e4
Create Date: 2026-05-15 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "18e1664ccddb"
down_revision = "71c1c1969e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cost_transactions",
        sa.Column("is_opening_balance", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("idx_is_opening_balance", "cost_transactions", ["is_opening_balance"])


def downgrade() -> None:
    op.drop_index("idx_is_opening_balance", table_name="cost_transactions")
    op.drop_column("cost_transactions", "is_opening_balance")
