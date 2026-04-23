"""schema_fixes_fk_indexes_array_tags_keyresults

Revision ID: dd1304cb0ac3
Revises: 1b16f64c4179
Create Date: 2026-04-23 16:20:47.299767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dd1304cb0ac3'
down_revision: Union[str, Sequence[str], None] = '1b16f64c4179'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add key_results table (FK -> goals CASCADE)
    op.create_table(
        'key_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('goal_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=False, server_default='0'),
        sa.Column('unit', sa.String(length=50), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], name='fk_key_results_goal_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. Drop the redundant junction table (Sprint.task_ids now derived from tasks.sprint_id)
    op.drop_table('sprint_task_ids')

    # 3. Convert tags TEXT (JSON) -> native Postgres ARRAY.
    #    asyncpg does not support subqueries in ALTER TABLE ... USING expressions,
    #    so we drop and recreate the column. Safe on a dev DB with no production data.
    op.execute("ALTER TABLE goals DROP COLUMN tags")
    op.execute("ALTER TABLE goals ADD COLUMN tags character varying[] NOT NULL DEFAULT '{}'")
    op.execute("ALTER TABLE tasks DROP COLUMN tags")
    op.execute("ALTER TABLE tasks ADD COLUMN tags character varying[] NOT NULL DEFAULT '{}'")

    # 4. Foreign keys on tasks
    op.create_foreign_key(
        'fk_tasks_sprint_id', 'tasks', 'sprints', ['sprint_id'], ['id'], ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_tasks_goal_id', 'tasks', 'goals', ['goal_id'], ['id'], ondelete='SET NULL'
    )

    # 5. Indexes on frequently filtered columns
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_tasks_sprint_id', 'tasks', ['sprint_id'])
    op.create_index('ix_tasks_goal_id', 'tasks', ['goal_id'])
    op.create_index('ix_tasks_scheduled_date', 'tasks', ['scheduled_date'])
    op.create_index('ix_tasks_task_type', 'tasks', ['task_type'])


def downgrade() -> None:
    op.drop_index('ix_tasks_task_type', table_name='tasks')
    op.drop_index('ix_tasks_scheduled_date', table_name='tasks')
    op.drop_index('ix_tasks_goal_id', table_name='tasks')
    op.drop_index('ix_tasks_sprint_id', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')

    op.drop_constraint('fk_tasks_goal_id', 'tasks', type_='foreignkey')
    op.drop_constraint('fk_tasks_sprint_id', 'tasks', type_='foreignkey')

    # Revert ARRAY -> TEXT (JSON); existing arrays become valid JSON arrays
    op.execute(
        "ALTER TABLE tasks ALTER COLUMN tags TYPE text "
        "USING array_to_json(tags)::text"
    )
    op.execute(
        "ALTER TABLE goals ALTER COLUMN tags TYPE text "
        "USING array_to_json(tags)::text"
    )

    op.create_table(
        'sprint_task_ids',
        sa.Column('sprint_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.Column('task_id', sa.UUID(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('sprint_id', 'task_id', name='sprint_task_ids_pkey'),
    )

    op.drop_table('key_results')
