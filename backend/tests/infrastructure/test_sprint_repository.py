import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository


def _sprint(name: str = "Sprint 1") -> Sprint:
    return Sprint(name, DateRange(date(2026, 5, 1), date(2026, 5, 14)))


@pytest.fixture
def repo(db_session: AsyncSession) -> PostgresSprintRepository:
    return PostgresSprintRepository(db_session)


# --- save / get_by_id ---

async def test_save_and_get(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    await repo.save(sprint)

    result = await repo.get_by_id(sprint.id)

    assert result is not None
    assert result.id == sprint.id
    assert result.name == "Sprint 1"
    assert result.status == SprintStatus.PLANNED
    assert result.date_range == DateRange(date(2026, 5, 1), date(2026, 5, 14))


async def test_get_missing_returns_none(repo: PostgresSprintRepository) -> None:
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_save_with_task_ids(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    sprint.add_task(t1)
    sprint.add_task(t2)
    await repo.save(sprint)

    result = await repo.get_by_id(sprint.id)
    assert result is not None
    assert set(result.task_ids) == {t1, t2}


async def test_save_updates_task_ids(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    t1 = uuid.uuid4()
    sprint.add_task(t1)
    await repo.save(sprint)

    t2 = uuid.uuid4()
    sprint.add_task(t2)
    sprint.remove_task(t1)
    await repo.save(sprint)

    result = await repo.get_by_id(sprint.id)
    assert result is not None
    assert t2 in result.task_ids
    assert t1 not in result.task_ids


async def test_save_updates_status(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    await repo.save(sprint)
    sprint.start()
    await repo.save(sprint)

    result = await repo.get_by_id(sprint.id)
    assert result is not None
    assert result.status == SprintStatus.ACTIVE


# --- delete ---

async def test_delete(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    await repo.save(sprint)
    await repo.delete(sprint.id)
    assert await repo.get_by_id(sprint.id) is None


async def test_delete_also_removes_task_ids(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    sprint.add_task(uuid.uuid4())
    await repo.save(sprint)
    await repo.delete(sprint.id)
    assert await repo.get_by_id(sprint.id) is None


async def test_delete_nonexistent_is_safe(repo: PostgresSprintRepository) -> None:
    await repo.delete(uuid.uuid4())


# --- list_all ---

async def test_list_all_empty(repo: PostgresSprintRepository) -> None:
    assert await repo.list_all() == []


async def test_list_all(repo: PostgresSprintRepository) -> None:
    s1 = _sprint("Sprint 1")
    s2 = _sprint("Sprint 2")
    await repo.save(s1)
    await repo.save(s2)

    results = await repo.list_all()
    ids = {s.id for s in results}
    assert s1.id in ids and s2.id in ids


# --- get_active ---

async def test_get_active_none_when_empty(repo: PostgresSprintRepository) -> None:
    assert await repo.get_active() is None


async def test_get_active_returns_active_sprint(repo: PostgresSprintRepository) -> None:
    planned = _sprint("Planned")
    active = _sprint("Active")
    active.start()

    await repo.save(planned)
    await repo.save(active)

    result = await repo.get_active()
    assert result is not None
    assert result.id == active.id
    assert result.status == SprintStatus.ACTIVE


async def test_get_active_none_when_only_planned(repo: PostgresSprintRepository) -> None:
    await repo.save(_sprint())
    assert await repo.get_active() is None
