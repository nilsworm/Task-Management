import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask
from src.domain.factory import TaskFactory
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus
from src.infrastructure.persistence.repositories.goal_repository import PostgresGoalRepository
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository
from src.infrastructure.persistence.repositories.task_repository import PostgresTaskRepository


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()


@pytest.fixture
def repo(db_session: AsyncSession) -> PostgresTaskRepository:
    return PostgresTaskRepository(db_session)


@pytest.fixture
def sprint_repo(db_session: AsyncSession) -> PostgresSprintRepository:
    return PostgresSprintRepository(db_session)


@pytest.fixture
def goal_repo(db_session: AsyncSession) -> PostgresGoalRepository:
    return PostgresGoalRepository(db_session)


# --- save / get_by_id ---

async def test_save_and_get_daily_task(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Write tests", scheduled_date=date(2026, 5, 1))
    await repo.save(task)

    result = await repo.get_by_id(task.id)

    assert result is not None
    assert isinstance(result, DailyTask)
    assert result.id == task.id
    assert result.title == "Write tests"
    assert result.status == TaskStatus.BACKLOG
    assert result.scheduled_date == date(2026, 5, 1)


async def test_save_and_get_sprint_task(
    repo: PostgresTaskRepository,
    sprint_repo: PostgresSprintRepository,
    factory: TaskFactory,
) -> None:
    from src.domain.sprint import Sprint
    from src.domain.value_objects import DateRange as DR
    sprint = Sprint("Sprint 1", DR(date(2026, 5, 1), date(2026, 5, 14)))
    await sprint_repo.save(sprint)

    task = factory.create_sprint("API endpoint", sprint_id=sprint.id, estimation=Estimation(5))
    await repo.save(task)

    result = await repo.get_by_id(task.id)

    assert result is not None
    assert isinstance(result, SprintTask)
    assert result.sprint_id == sprint.id
    assert result.story_points == 5


async def test_save_and_get_goal(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 6, 30))
    task = factory.create_goal("Learn Rust", date_range=dr)
    await repo.save(task)

    result = await repo.get_by_id(task.id)

    assert result is not None
    assert isinstance(result, LongTermGoal)
    assert result.date_range == dr


async def test_save_and_get_milestone(
    repo: PostgresTaskRepository,
    goal_repo: PostgresGoalRepository,
    factory: TaskFactory,
) -> None:
    goal = LongTermGoal("Parent goal")
    await goal_repo.save(goal)

    task = factory.create_milestone("v1.0", due_date=date(2026, 3, 31), goal_id=goal.id)
    await repo.save(task)

    result = await repo.get_by_id(task.id)

    assert result is not None
    assert isinstance(result, Milestone)
    assert result.due_date == date(2026, 3, 31)
    assert result.goal_id == goal.id


async def test_save_with_tags(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Task", tags=frozenset({Tag("backend"), Tag("urgent")}))
    await repo.save(task)

    result = await repo.get_by_id(task.id)
    assert result is not None
    assert Tag("backend") in result.tags
    assert Tag("urgent") in result.tags


async def test_get_missing_returns_none(repo: PostgresTaskRepository) -> None:
    assert await repo.get_by_id(uuid.uuid4()) is None


async def test_save_overwrites_existing(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Original")
    await repo.save(task)

    task.update_title("Updated")
    task.transition_to(TaskStatus.TODO)
    await repo.save(task)

    result = await repo.get_by_id(task.id)
    assert result is not None
    assert result.title == "Updated"
    assert result.status == TaskStatus.TODO


async def test_save_preserves_priority_and_estimation(
    repo: PostgresTaskRepository, factory: TaskFactory
) -> None:
    task = factory.create_daily("Task", priority=Priority.CRITICAL, estimation=Estimation(13))
    await repo.save(task)

    result = await repo.get_by_id(task.id)
    assert result is not None
    assert result.priority == Priority.CRITICAL
    assert result.estimation == Estimation(13)


# --- delete ---

async def test_delete(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Task")
    await repo.save(task)
    await repo.delete(task.id)
    assert await repo.get_by_id(task.id) is None


async def test_delete_nonexistent_is_safe(repo: PostgresTaskRepository) -> None:
    await repo.delete(uuid.uuid4())  # must not raise


# --- list_all ---

async def test_list_all_empty(repo: PostgresTaskRepository) -> None:
    assert await repo.list_all() == []


async def test_list_all(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    t1 = factory.create_daily("T1")
    t2 = factory.create_sprint("T2")
    await repo.save(t1)
    await repo.save(t2)

    results = await repo.list_all()
    ids = {t.id for t in results}
    assert t1.id in ids and t2.id in ids


# --- list_by_status ---

async def test_list_by_status(repo: PostgresTaskRepository, factory: TaskFactory) -> None:
    t_backlog = factory.create_daily("Backlog")
    t_todo = factory.create_daily("Todo")
    t_todo.transition_to(TaskStatus.TODO)

    await repo.save(t_backlog)
    await repo.save(t_todo)

    backlog = await repo.list_by_status(TaskStatus.BACKLOG)
    todo = await repo.list_by_status(TaskStatus.TODO)

    assert len(backlog) == 1 and backlog[0].id == t_backlog.id
    assert len(todo) == 1 and todo[0].id == t_todo.id


async def test_list_by_status_empty(repo: PostgresTaskRepository) -> None:
    assert await repo.list_by_status(TaskStatus.DONE) == []


# --- list_by_sprint ---

async def test_list_by_sprint(
    repo: PostgresTaskRepository,
    sprint_repo: PostgresSprintRepository,
    factory: TaskFactory,
) -> None:
    from src.domain.sprint import Sprint
    from src.domain.value_objects import DateRange as DR
    dr = DR(date(2026, 5, 1), date(2026, 5, 14))
    s1 = Sprint("Sprint 1", dr)
    s2 = Sprint("Sprint 2", dr)
    await sprint_repo.save(s1)
    await sprint_repo.save(s2)

    t1 = factory.create_sprint("In sprint", sprint_id=s1.id)
    t2 = factory.create_sprint("Other sprint", sprint_id=s2.id)
    t3 = factory.create_daily("Not a sprint task")

    await repo.save(t1)
    await repo.save(t2)
    await repo.save(t3)

    results = await repo.list_by_sprint(s1.id)
    assert len(results) == 1
    assert results[0].id == t1.id
    assert isinstance(results[0], SprintTask)


async def test_list_by_sprint_empty(repo: PostgresTaskRepository) -> None:
    assert await repo.list_by_sprint(uuid.uuid4()) == []
