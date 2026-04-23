import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import LongTermGoal
from src.domain.value_objects import DateRange, Priority, Tag, TaskStatus
from src.infrastructure.persistence.repositories.goal_repository import PostgresGoalRepository


def _goal(title: str = "Learn Rust") -> LongTermGoal:
    return LongTermGoal(title)


@pytest.fixture
def repo(db_session: AsyncSession) -> PostgresGoalRepository:
    return PostgresGoalRepository(db_session)


# --- save / get_by_id ---

async def test_save_and_get(repo: PostgresGoalRepository) -> None:
    goal = _goal()
    await repo.save(goal)

    result = await repo.get_by_id(goal.id)

    assert result is not None
    assert result.id == goal.id
    assert result.title == "Learn Rust"
    assert result.status == TaskStatus.BACKLOG
    assert result.priority == Priority.MEDIUM


async def test_get_missing_returns_none(repo: PostgresGoalRepository) -> None:
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_save_with_date_range(repo: PostgresGoalRepository) -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 12, 31))
    goal = LongTermGoal("Yearly goal", date_range=dr)
    await repo.save(goal)

    result = await repo.get_by_id(goal.id)
    assert result is not None
    assert result.date_range == dr


async def test_save_without_date_range(repo: PostgresGoalRepository) -> None:
    goal = _goal()
    await repo.save(goal)

    result = await repo.get_by_id(goal.id)
    assert result is not None
    assert result.date_range is None


async def test_save_with_tags(repo: PostgresGoalRepository) -> None:
    goal = LongTermGoal("Tagged goal", tags=frozenset({Tag("learning"), Tag("q1")}))
    await repo.save(goal)

    result = await repo.get_by_id(goal.id)
    assert result is not None
    assert Tag("learning") in result.tags
    assert Tag("q1") in result.tags


async def test_save_overwrites_existing(repo: PostgresGoalRepository) -> None:
    goal = _goal()
    await repo.save(goal)

    goal.update_title("Updated goal")
    goal.update_priority(Priority.HIGH)
    await repo.save(goal)

    result = await repo.get_by_id(goal.id)
    assert result is not None
    assert result.title == "Updated goal"
    assert result.priority == Priority.HIGH


# --- delete ---

async def test_delete(repo: PostgresGoalRepository) -> None:
    goal = _goal()
    await repo.save(goal)
    await repo.delete(goal.id)
    assert await repo.get_by_id(goal.id) is None


async def test_delete_nonexistent_is_safe(repo: PostgresGoalRepository) -> None:
    await repo.delete(uuid.uuid4())


# --- list_all ---

async def test_list_all_empty(repo: PostgresGoalRepository) -> None:
    assert await repo.list_all() == []


async def test_list_all(repo: PostgresGoalRepository) -> None:
    g1 = _goal("Goal 1")
    g2 = _goal("Goal 2")
    await repo.save(g1)
    await repo.save(g2)

    results = await repo.list_all()
    ids = {g.id for g in results}
    assert g1.id in ids and g2.id in ids
