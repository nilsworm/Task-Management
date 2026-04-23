"""API-level tests for GET /dashboard."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_event_bus, get_goal_repo, get_sprint_repo, get_task_repo
from src.domain.events import InMemoryEventBus
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange
from src.main import app
from tests.application.conftest import (
    InMemoryGoalRepository,
    InMemorySprintRepository,
    InMemoryTaskRepository,
)

_factory = TaskFactory()
_dr = DateRange(date(2026, 5, 1), date(2026, 5, 14))


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
def client(
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
    goal_repo: InMemoryGoalRepository,
) -> TestClient:
    bus = InMemoryEventBus()
    app.dependency_overrides[get_task_repo] = lambda: task_repo
    app.dependency_overrides[get_sprint_repo] = lambda: sprint_repo
    app.dependency_overrides[get_goal_repo] = lambda: goal_repo
    app.dependency_overrides[get_event_bus] = lambda: bus
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_dashboard_empty(client: TestClient) -> None:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_tasks"] == 0
    assert data["total_goals"] == 0
    assert data["active_sprint"] is None
    counts = data["task_counts"]
    assert counts["backlog"] == 0
    assert counts["done"] == 0


def test_dashboard_task_counts(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
) -> None:
    import asyncio
    t1 = _factory.create_daily("Task 1")
    t2 = _factory.create_daily("Task 2")
    t2.transition_to(__import__("src.domain.value_objects", fromlist=["TaskStatus"]).TaskStatus.TODO)
    asyncio.run(task_repo.save(t1))
    asyncio.run(task_repo.save(t2))

    data = client.get("/dashboard").json()
    assert data["total_tasks"] == 2
    assert data["task_counts"]["backlog"] == 1
    assert data["task_counts"]["todo"] == 1


def test_dashboard_with_active_sprint(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    import asyncio
    from src.domain.value_objects import TaskStatus

    sprint = Sprint("Sprint 1", _dr)
    sprint.start()
    asyncio.run(sprint_repo.save(sprint))

    t1 = _factory.create_sprint("Task A", sprint_id=sprint.id)
    t2 = _factory.create_sprint("Task B", sprint_id=sprint.id)
    t2.transition_to(TaskStatus.TODO)
    t2.transition_to(TaskStatus.IN_PROGRESS)
    t2.transition_to(TaskStatus.REVIEW)
    t2.transition_to(TaskStatus.DONE)
    asyncio.run(task_repo.save(t1))
    asyncio.run(task_repo.save(t2))
    sprint.add_task(t1.id)
    sprint.add_task(t2.id)
    asyncio.run(sprint_repo.save(sprint))

    data = client.get("/dashboard").json()
    active = data["active_sprint"]
    assert active is not None
    assert active["name"] == "Sprint 1"
    assert active["status"] == "active"
    assert active["total_tasks"] == 2
    assert active["done_tasks"] == 1
    assert active["completion_percent"] == 50.0


def test_dashboard_goal_count(
    client: TestClient,
    goal_repo: InMemoryGoalRepository,
) -> None:
    import asyncio
    from src.domain.entities import LongTermGoal

    asyncio.run(goal_repo.save(LongTermGoal("Goal 1")))
    asyncio.run(goal_repo.save(LongTermGoal("Goal 2")))

    data = client.get("/dashboard").json()
    assert data["total_goals"] == 2
