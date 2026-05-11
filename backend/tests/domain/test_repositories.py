"""
Contract tests for repository interfaces using in-memory mock implementations.
Every future Postgres implementation must satisfy the same contracts.
"""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import pytest

from src.domain.entities import DailyTask, LongTermGoal, SprintTask, Task
from src.domain.factory import TaskFactory
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange, Estimation, Priority, TaskStatus


# ---------------------------------------------------------------------------
# In-memory mock implementations
# ---------------------------------------------------------------------------

class InMemoryTaskRepository(ITaskRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Task] = {}

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return self._store.get(task_id)

    async def save(self, task: Task) -> None:
        self._store[task.id] = task

    async def delete(self, task_id: uuid.UUID) -> None:
        self._store.pop(task_id, None)

    async def list_all(self) -> list[Task]:
        return list(self._store.values())

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._store.values() if t.status == status]

    async def list_by_sprint(
        self,
        sprint_id: uuid.UUID,
        status_filter: TaskStatus | None = None,
    ) -> list[SprintTask]:
        tasks = [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id == sprint_id
        ]
        if status_filter is not None:
            tasks = [t for t in tasks if t.status == status_filter]
        return tasks

    async def list_by_sprint_ids(
        self, sprint_ids: list[uuid.UUID]
    ) -> list[SprintTask]:
        return [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id in sprint_ids
        ]


class InMemorySprintRepository(ISprintRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Sprint] = {}

    async def get_by_id(self, sprint_id: uuid.UUID) -> Sprint | None:
        return self._store.get(sprint_id)

    async def save(self, sprint: Sprint) -> None:
        self._store[sprint.id] = sprint

    async def delete(self, sprint_id: uuid.UUID) -> None:
        self._store.pop(sprint_id, None)

    async def list_all(self) -> list[Sprint]:
        return list(self._store.values())

    async def get_active(self) -> Sprint | None:
        for sprint in self._store.values():
            if sprint.status is SprintStatus.ACTIVE:
                return sprint
        return None


class InMemoryGoalRepository(IGoalRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, LongTermGoal] = {}
        self._key_results: dict[uuid.UUID, Any] = {}

    async def get_by_id(self, goal_id: uuid.UUID) -> LongTermGoal | None:
        return self._store.get(goal_id)

    async def save(self, goal: LongTermGoal) -> None:
        self._store[goal.id] = goal

    async def delete(self, goal_id: uuid.UUID) -> None:
        self._store.pop(goal_id, None)

    async def list_all(self) -> list[LongTermGoal]:
        return list(self._store.values())

    async def list_key_results(self, goal_id: uuid.UUID) -> list[Any]:
        return [kr for kr in self._key_results.values() if kr.goal_id == goal_id]

    async def list_all_key_results(self) -> list[Any]:
        return list(self._key_results.values())

    async def get_key_result(self, key_result_id: uuid.UUID) -> Any | None:
        return self._key_results.get(key_result_id)

    async def save_key_result(self, key_result: Any) -> None:
        self._key_results[key_result.id] = key_result

    async def delete_key_result(self, key_result_id: uuid.UUID) -> None:
        self._key_results.pop(key_result_id, None)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def sprint_repo() -> InMemorySprintRepository:
    return InMemorySprintRepository()


@pytest.fixture
def goal_repo() -> InMemoryGoalRepository:
    return InMemoryGoalRepository()


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()


def _sprint(name: str = "Sprint 1") -> Sprint:
    return Sprint(name, DateRange(date(2026, 5, 1), date(2026, 5, 14)))


def _goal(title: str = "Learn Rust") -> LongTermGoal:
    return LongTermGoal(title)


# ---------------------------------------------------------------------------
# ITaskRepository contract tests
# ---------------------------------------------------------------------------

async def test_task_repo_save_and_get(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Write docs")
    await task_repo.save(task)
    result = await task_repo.get_by_id(task.id)
    assert result is task


async def test_task_repo_get_missing_returns_none(task_repo: InMemoryTaskRepository) -> None:
    result = await task_repo.get_by_id(uuid.uuid4())
    assert result is None


async def test_task_repo_save_overwrites(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Original")
    await task_repo.save(task)
    task.update_title("Updated")
    await task_repo.save(task)
    result = await task_repo.get_by_id(task.id)
    assert result is not None
    assert result.title == "Updated"


async def test_task_repo_delete(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)
    await task_repo.delete(task.id)
    assert await task_repo.get_by_id(task.id) is None


async def test_task_repo_delete_nonexistent_is_safe(task_repo: InMemoryTaskRepository) -> None:
    await task_repo.delete(uuid.uuid4())  # must not raise


async def test_task_repo_list_all_empty(task_repo: InMemoryTaskRepository) -> None:
    assert await task_repo.list_all() == []


async def test_task_repo_list_all(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    t1 = factory.create_daily("T1")
    t2 = factory.create_daily("T2")
    await task_repo.save(t1)
    await task_repo.save(t2)
    all_tasks = await task_repo.list_all()
    assert len(all_tasks) == 2
    ids = {t.id for t in all_tasks}
    assert t1.id in ids and t2.id in ids


async def test_task_repo_list_by_status(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    t_backlog = factory.create_daily("Backlog task")
    t_todo = factory.create_daily("Todo task")
    t_todo.transition_to(TaskStatus.TODO)
    await task_repo.save(t_backlog)
    await task_repo.save(t_todo)

    backlog = await task_repo.list_by_status(TaskStatus.BACKLOG)
    todo = await task_repo.list_by_status(TaskStatus.TODO)

    assert len(backlog) == 1
    assert backlog[0].id == t_backlog.id
    assert len(todo) == 1
    assert todo[0].id == t_todo.id


async def test_task_repo_list_by_status_empty(task_repo: InMemoryTaskRepository) -> None:
    assert await task_repo.list_by_status(TaskStatus.DONE) == []


async def test_task_repo_list_by_sprint(task_repo: InMemoryTaskRepository, factory: TaskFactory) -> None:
    sid = uuid.uuid4()
    other_sid = uuid.uuid4()
    t1 = factory.create_sprint("Sprint task", sprint_id=sid)
    t2 = factory.create_sprint("Other sprint", sprint_id=other_sid)
    t3 = factory.create_daily("Daily task")
    await task_repo.save(t1)
    await task_repo.save(t2)
    await task_repo.save(t3)

    results = await task_repo.list_by_sprint(sid)
    assert len(results) == 1
    assert results[0].id == t1.id


async def test_task_repo_list_by_sprint_empty(task_repo: InMemoryTaskRepository) -> None:
    assert await task_repo.list_by_sprint(uuid.uuid4()) == []


# ---------------------------------------------------------------------------
# ISprintRepository contract tests
# ---------------------------------------------------------------------------

async def test_sprint_repo_save_and_get(sprint_repo: InMemorySprintRepository) -> None:
    sprint = _sprint()
    await sprint_repo.save(sprint)
    result = await sprint_repo.get_by_id(sprint.id)
    assert result is sprint


async def test_sprint_repo_get_missing_returns_none(sprint_repo: InMemorySprintRepository) -> None:
    assert await sprint_repo.get_by_id(uuid.uuid4()) is None


async def test_sprint_repo_delete(sprint_repo: InMemorySprintRepository) -> None:
    sprint = _sprint()
    await sprint_repo.save(sprint)
    await sprint_repo.delete(sprint.id)
    assert await sprint_repo.get_by_id(sprint.id) is None


async def test_sprint_repo_delete_nonexistent_is_safe(sprint_repo: InMemorySprintRepository) -> None:
    await sprint_repo.delete(uuid.uuid4())


async def test_sprint_repo_list_all(sprint_repo: InMemorySprintRepository) -> None:
    s1 = _sprint("Sprint 1")
    s2 = _sprint("Sprint 2")
    await sprint_repo.save(s1)
    await sprint_repo.save(s2)
    all_sprints = await sprint_repo.list_all()
    assert len(all_sprints) == 2


async def test_sprint_repo_get_active_none_when_empty(sprint_repo: InMemorySprintRepository) -> None:
    assert await sprint_repo.get_active() is None


async def test_sprint_repo_get_active_returns_active_sprint(sprint_repo: InMemorySprintRepository) -> None:
    planned = _sprint("Planned")
    active = _sprint("Active")
    active.start()
    await sprint_repo.save(planned)
    await sprint_repo.save(active)
    result = await sprint_repo.get_active()
    assert result is active


async def test_sprint_repo_get_active_none_when_only_planned(sprint_repo: InMemorySprintRepository) -> None:
    await sprint_repo.save(_sprint("Planned"))
    assert await sprint_repo.get_active() is None


# ---------------------------------------------------------------------------
# IGoalRepository contract tests
# ---------------------------------------------------------------------------

async def test_goal_repo_save_and_get(goal_repo: InMemoryGoalRepository) -> None:
    goal = _goal()
    await goal_repo.save(goal)
    result = await goal_repo.get_by_id(goal.id)
    assert result is goal


async def test_goal_repo_get_missing_returns_none(goal_repo: InMemoryGoalRepository) -> None:
    assert await goal_repo.get_by_id(uuid.uuid4()) is None


async def test_goal_repo_delete(goal_repo: InMemoryGoalRepository) -> None:
    goal = _goal()
    await goal_repo.save(goal)
    await goal_repo.delete(goal.id)
    assert await goal_repo.get_by_id(goal.id) is None


async def test_goal_repo_delete_nonexistent_is_safe(goal_repo: InMemoryGoalRepository) -> None:
    await goal_repo.delete(uuid.uuid4())


async def test_goal_repo_list_all(goal_repo: InMemoryGoalRepository) -> None:
    g1 = _goal("Goal 1")
    g2 = _goal("Goal 2")
    await goal_repo.save(g1)
    await goal_repo.save(g2)
    all_goals = await goal_repo.list_all()
    assert len(all_goals) == 2
    ids = {g.id for g in all_goals}
    assert g1.id in ids and g2.id in ids


async def test_goal_repo_list_all_empty(goal_repo: InMemoryGoalRepository) -> None:
    assert await goal_repo.list_all() == []


# ---------------------------------------------------------------------------
# Interfaces are abstract
# ---------------------------------------------------------------------------

def test_itask_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        ITaskRepository()  # type: ignore[abstract]


def test_isprint_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        ISprintRepository()  # type: ignore[abstract]


def test_igoal_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        IGoalRepository()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# Sprint entity (minimal, used by ISprintRepository)
# ---------------------------------------------------------------------------

def test_sprint_defaults() -> None:
    dr = DateRange(date(2026, 5, 1), date(2026, 5, 14))
    s = Sprint("Sprint 1", dr)
    assert s.name == "Sprint 1"
    assert s.status is SprintStatus.PLANNED
    assert s.task_ids == []
    assert isinstance(s.id, uuid.UUID)


def test_sprint_empty_name_raises() -> None:
    with pytest.raises(ValueError):
        Sprint("  ", DateRange(date(2026, 5, 1), date(2026, 5, 14)))


def test_sprint_add_task() -> None:
    s = _sprint()
    tid = uuid.uuid4()
    s.add_task(tid)
    assert tid in s.task_ids


def test_sprint_add_task_idempotent() -> None:
    s = _sprint()
    tid = uuid.uuid4()
    s.add_task(tid)
    s.add_task(tid)
    assert s.task_ids.count(tid) == 1


def test_sprint_remove_task() -> None:
    s = _sprint()
    tid = uuid.uuid4()
    s.add_task(tid)
    s.remove_task(tid)
    assert tid not in s.task_ids


def test_sprint_start() -> None:
    s = _sprint()
    s.start()
    assert s.status is SprintStatus.ACTIVE


def test_sprint_start_from_wrong_status_raises() -> None:
    s = _sprint()
    s.start()
    with pytest.raises(ValueError, match="active"):
        s.start()


def test_sprint_complete() -> None:
    s = _sprint()
    s.start()
    s.complete()
    assert s.status is SprintStatus.COMPLETED


def test_sprint_complete_from_wrong_status_raises() -> None:
    s = _sprint()
    with pytest.raises(ValueError, match="planned"):
        s.complete()


def test_sprint_cancel_from_planned() -> None:
    s = _sprint()
    s.cancel()
    assert s.status is SprintStatus.CANCELLED


def test_sprint_cancel_from_active() -> None:
    s = _sprint()
    s.start()
    s.cancel()
    assert s.status is SprintStatus.CANCELLED


def test_sprint_cancel_from_completed_raises() -> None:
    s = _sprint()
    s.start()
    s.complete()
    with pytest.raises(ValueError, match="completed"):
        s.cancel()
