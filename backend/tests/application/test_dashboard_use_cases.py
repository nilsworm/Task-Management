"""Unit tests for GetDashboardUseCase."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from src.application.use_cases.dashboard_use_cases import GetDashboardUseCase
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange, TaskStatus

from .conftest import InMemoryGoalRepository, InMemorySprintRepository, InMemoryTaskRepository

_factory = TaskFactory()
_dr = DateRange(date(2026, 5, 1), date(2026, 5, 14))


async def test_dashboard_empty_state(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.total_tasks == 0
    assert data.total_goals == 0
    assert data.active_sprint is None
    assert data.backlog == 0
    assert data.done == 0


async def test_dashboard_counts_tasks_by_status(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    t1 = _factory.create_daily("Task A")
    t2 = _factory.create_daily("Task B")
    t2.transition_to(TaskStatus.TODO)
    t3 = _factory.create_daily("Task C")
    t3.transition_to(TaskStatus.TODO)
    t3.transition_to(TaskStatus.IN_PROGRESS)
    await task_repo.save(t1)
    await task_repo.save(t2)
    await task_repo.save(t3)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.total_tasks == 3
    assert data.backlog == 1
    assert data.todo == 1
    assert data.in_progress == 1
    assert data.done == 0


async def test_dashboard_active_sprint_completion(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Sprint 1", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    t1 = _factory.create_sprint("Task A", sprint_id=sprint.id)
    t2 = _factory.create_sprint("Task B", sprint_id=sprint.id)
    t2.transition_to(TaskStatus.TODO)
    t2.transition_to(TaskStatus.IN_PROGRESS)
    t2.transition_to(TaskStatus.REVIEW)
    t2.transition_to(TaskStatus.DONE)
    await task_repo.save(t1)
    await task_repo.save(t2)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is not None
    assert data.active_sprint.name == "Sprint 1"
    assert data.active_sprint.total_tasks == 2
    assert data.active_sprint.done_tasks == 1
    assert data.active_sprint.completion_percent == 50.0


async def test_dashboard_no_active_sprint_when_planned(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Planned Sprint", _dr)
    await sprint_repo.save(sprint)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is None


async def test_dashboard_sprint_zero_tasks_completion(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> None:
    sprint = Sprint("Empty Sprint", _dr)
    sprint.start()
    await sprint_repo.save(sprint)

    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()

    assert data.active_sprint is not None
    assert data.active_sprint.completion_percent == 0.0
