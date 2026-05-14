"""add transaction import_source field

Revision ID: 71c1c1969e4
Revises: a3f2e1d9c8b7
Create Date: 2026-05-14 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "71c1c1969e4"
down_revision = "a3f2e1d9c8b7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cost_transactions",
        sa.Column("import_source", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cost_transactions", "import_source")
