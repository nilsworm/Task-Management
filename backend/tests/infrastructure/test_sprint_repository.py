import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository
from src.infrastructure.persistence.repositories.task_repository import PostgresTaskRepository


def _sprint(name: str = "Sprint 1") -> Sprint:
    return Sprint(name, DateRange(date(2026, 5, 1), date(2026, 5, 14)))


@pytest.fixture
def repo(db_session: AsyncSession) -> PostgresSprintRepository:
    return PostgresSprintRepository(db_session)


@pytest.fixture
def task_repo(db_session: AsyncSession) -> PostgresTaskRepository:
    return PostgresTaskRepository(db_session)


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()


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


async def test_save_with_task_ids(
    repo: PostgresSprintRepository,
    task_repo: PostgresTaskRepository,
    factory: TaskFactory,
) -> None:
    sprint = _sprint()
    await repo.save(sprint)

    t1 = factory.create_sprint("Task 1", sprint_id=sprint.id)
    t2 = factory.create_sprint("Task 2", sprint_id=sprint.id)
    await task_repo.save(t1)
    await task_repo.save(t2)

    result = await repo.get_by_id(sprint.id)
    assert result is not None
    assert set(result.task_ids) == {t1.id, t2.id}


async def test_task_ids_empty_for_fresh_sprint(repo: PostgresSprintRepository) -> None:
    sprint = _sprint()
    await repo.save(sprint)

    result = await repo.get_by_id(sprint.id)
    assert result is not None
    assert result.task_ids == []


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


async def test_delete_sets_task_sprint_id_to_null(
    repo: PostgresSprintRepository,
    task_repo: PostgresTaskRepository,
    factory: TaskFactory,
) -> None:
    sprint = _sprint()
    await repo.save(sprint)
    task = factory.create_sprint("Task", sprint_id=sprint.id)
    await task_repo.save(task)

    await repo.delete(sprint.id)

    # Sprint gone
    assert await repo.get_by_id(sprint.id) is None
    # Task still exists (ON DELETE SET NULL)
    saved_task = await task_repo.get_by_id(task.id)
    assert saved_task is not None


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
