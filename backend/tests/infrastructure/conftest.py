"""
Integration test setup: creates taskmanager_test database, runs schema via
SQLAlchemy metadata, provides per-test AsyncSession, truncates after each test.
"""
from __future__ import annotations

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.infrastructure.database import Base

# Register all models with Base.metadata before create_all
import src.infrastructure.persistence.models.goal_model  # noqa: F401
import src.infrastructure.persistence.models.sprint_model  # noqa: F401
import src.infrastructure.persistence.models.task_model  # noqa: F401

TEST_DB_URL = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager_test"
_ADMIN_URL = "postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/postgres"
_TABLES = "tasks, sprints, sprint_task_ids, goals"


# ---------------------------------------------------------------------------
# DB lifecycle — runs synchronously via asyncio.run() so pytest hooks work
# ---------------------------------------------------------------------------

def pytest_configure(config: pytest.Config) -> None:
    asyncio.run(_create_test_db())


def pytest_unconfigure(config: pytest.Config) -> None:
    asyncio.run(_drop_test_db())


async def _create_test_db() -> None:
    admin = create_async_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = 'taskmanager_test'")
        )
        if not exists:
            await conn.execute(text("CREATE DATABASE taskmanager_test"))
    await admin.dispose()

    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


async def _drop_test_db() -> None:
    admin = create_async_engine(_ADMIN_URL, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        await conn.execute(
            text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                "WHERE datname = 'taskmanager_test' AND pid <> pg_backend_pid()"
            )
        )
        await conn.execute(text("DROP DATABASE IF EXISTS taskmanager_test"))
    await admin.dispose()


# ---------------------------------------------------------------------------
# Per-test AsyncSession (NullPool avoids event-loop affinity issues)
# ---------------------------------------------------------------------------

@pytest.fixture
async def db_session() -> AsyncSession:
    engine = create_async_engine(TEST_DB_URL, echo=False, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    async with engine.connect() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {_TABLES} RESTART IDENTITY CASCADE"))
        await conn.commit()
    await engine.dispose()
