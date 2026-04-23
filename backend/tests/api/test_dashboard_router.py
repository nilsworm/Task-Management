"""API-level tests for GET /dashboard and sub-endpoints."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_event_bus, get_goal_repo, get_sprint_repo, get_task_repo
from src.domain.entities import KeyResult, LongTermGoal
from src.domain.events import InMemoryEventBus
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange, Estimation, TaskStatus
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


# ---------------------------------------------------------------------------
# GET /dashboard
# ---------------------------------------------------------------------------

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
    t2.transition_to(TaskStatus.TODO)
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
    asyncio.run(goal_repo.save(LongTermGoal("Goal 1")))
    asyncio.run(goal_repo.save(LongTermGoal("Goal 2")))

    data = client.get("/dashboard").json()
    assert data["total_goals"] == 2


# ---------------------------------------------------------------------------
# GET /dashboard/metrics
# ---------------------------------------------------------------------------

def test_metrics_empty(client: TestClient) -> None:
    resp = client.get("/dashboard/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["completion_rate"] == 0.0
    counts = data["task_counts"]
    assert counts["backlog"] == 0
    assert counts["done"] == 0


def test_metrics_completion_rate(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
) -> None:
    import asyncio
    t_done = _factory.create_daily("Done")
    t_done.transition_to(TaskStatus.TODO)
    t_done.transition_to(TaskStatus.IN_PROGRESS)
    t_done.transition_to(TaskStatus.REVIEW)
    t_done.transition_to(TaskStatus.DONE)
    t_backlog = _factory.create_daily("Backlog")
    asyncio.run(task_repo.save(t_done))
    asyncio.run(task_repo.save(t_backlog))

    data = client.get("/dashboard/metrics").json()
    assert data["task_counts"]["done"] == 1
    assert data["task_counts"]["backlog"] == 1
    assert data["completion_rate"] == 50.0


def test_metrics_cancelled_excluded_from_rate(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
) -> None:
    import asyncio
    t_done = _factory.create_daily("Done")
    t_done.transition_to(TaskStatus.TODO)
    t_done.transition_to(TaskStatus.IN_PROGRESS)
    t_done.transition_to(TaskStatus.REVIEW)
    t_done.transition_to(TaskStatus.DONE)
    t_cancelled = _factory.create_daily("Cancelled")
    t_cancelled.transition_to(TaskStatus.CANCELLED)
    asyncio.run(task_repo.save(t_done))
    asyncio.run(task_repo.save(t_cancelled))

    data = client.get("/dashboard/metrics").json()
    assert data["completion_rate"] == 100.0


# ---------------------------------------------------------------------------
# GET /dashboard/burndown
# ---------------------------------------------------------------------------

def test_burndown_no_active_sprint_returns_404(client: TestClient) -> None:
    resp = client.get("/dashboard/burndown")
    assert resp.status_code == 404


def test_burndown_active_sprint(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    import asyncio
    sprint = Sprint("Sprint 1", _dr)
    sprint.start()
    asyncio.run(sprint_repo.save(sprint))

    t = _factory.create_sprint("Task", sprint_id=sprint.id)
    t.set_estimation(Estimation(story_points=10))
    asyncio.run(task_repo.save(t))

    resp = client.get("/dashboard/burndown")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sprint_name"] == "Sprint 1"
    assert data["total_points"] == 10
    assert data["actual_remaining"] == 10
    assert len(data["ideal_line"]) == 14
    assert data["ideal_line"][0]["remaining_points"] == 10
    assert data["ideal_line"][-1]["remaining_points"] == 0


def test_burndown_by_sprint_id(
    client: TestClient,
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
) -> None:
    import asyncio
    sprint = Sprint("Completed", _dr)
    sprint.start()
    sprint.complete()
    asyncio.run(sprint_repo.save(sprint))

    resp = client.get(f"/dashboard/burndown?sprint_id={sprint.id}")
    assert resp.status_code == 200
    assert resp.json()["sprint_name"] == "Completed"


def test_burndown_unknown_sprint_id_returns_404(client: TestClient) -> None:
    resp = client.get(f"/dashboard/burndown?sprint_id={uuid.uuid4()}")
    assert resp.status_code == 404


def test_burndown_actual_remaining_reflects_done_tasks(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    import asyncio
    sprint = Sprint("Sprint", _dr)
    sprint.start()
    asyncio.run(sprint_repo.save(sprint))

    t_done = _factory.create_sprint("Done task", sprint_id=sprint.id)
    t_done.set_estimation(Estimation(story_points=6))
    t_done.transition_to(TaskStatus.TODO)
    t_done.transition_to(TaskStatus.IN_PROGRESS)
    t_done.transition_to(TaskStatus.REVIEW)
    t_done.transition_to(TaskStatus.DONE)
    t_open = _factory.create_sprint("Open task", sprint_id=sprint.id)
    t_open.set_estimation(Estimation(story_points=4))
    asyncio.run(task_repo.save(t_done))
    asyncio.run(task_repo.save(t_open))

    data = client.get("/dashboard/burndown").json()
    assert data["total_points"] == 10
    assert data["actual_remaining"] == 4


# ---------------------------------------------------------------------------
# GET /dashboard/velocity
# ---------------------------------------------------------------------------

def test_velocity_no_completed_sprints(client: TestClient) -> None:
    resp = client.get("/dashboard/velocity")
    assert resp.status_code == 200
    data = resp.json()
    assert data["sprints"] == []
    assert data["average_velocity"] == 0.0


def test_velocity_returns_completed_sprints(
    client: TestClient,
    task_repo: InMemoryTaskRepository,
    sprint_repo: InMemorySprintRepository,
) -> None:
    import asyncio
    sprint = Sprint("Done Sprint", _dr)
    sprint.start()
    sprint.complete()
    asyncio.run(sprint_repo.save(sprint))

    t = _factory.create_sprint("Task", sprint_id=sprint.id)
    t.set_estimation(Estimation(story_points=8))
    t.transition_to(TaskStatus.TODO)
    t.transition_to(TaskStatus.IN_PROGRESS)
    t.transition_to(TaskStatus.REVIEW)
    t.transition_to(TaskStatus.DONE)
    asyncio.run(task_repo.save(t))

    data = client.get("/dashboard/velocity").json()
    assert len(data["sprints"]) == 1
    assert data["sprints"][0]["completed_points"] == 8
    assert data["average_velocity"] == 8.0


def test_velocity_last_n_parameter(
    client: TestClient,
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
) -> None:
    import asyncio
    for i in range(3):
        s = Sprint(f"Sprint {i}", _dr)
        s.start()
        s.complete()
        asyncio.run(sprint_repo.save(s))

    data = client.get("/dashboard/velocity?last_n=2").json()
    assert len(data["sprints"]) == 2


# ---------------------------------------------------------------------------
# GET /dashboard/goal-progress
# ---------------------------------------------------------------------------

def _kr(goal_id: uuid.UUID, current: float, target: float) -> KeyResult:
    now = datetime.now(timezone.utc)
    return KeyResult(
        id=uuid.uuid4(),
        goal_id=goal_id,
        title="KR",
        description="",
        target_value=target,
        current_value=current,
        unit="units",
        created_at=now,
        updated_at=now,
    )


def test_goal_progress_empty(client: TestClient) -> None:
    resp = client.get("/dashboard/goal-progress")
    assert resp.status_code == 200
    assert resp.json()["goals"] == []


def test_goal_progress_no_krs(
    client: TestClient,
    goal_repo: InMemoryGoalRepository,
) -> None:
    import asyncio
    goal = LongTermGoal("Master Go")
    asyncio.run(goal_repo.save(goal))

    data = client.get("/dashboard/goal-progress").json()
    assert len(data["goals"]) == 1
    assert data["goals"][0]["progress_percent"] == 0.0
    assert data["goals"][0]["key_results_count"] == 0


def test_goal_progress_with_krs(
    client: TestClient,
    goal_repo: InMemoryGoalRepository,
) -> None:
    import asyncio
    goal = LongTermGoal("Ship product")
    asyncio.run(goal_repo.save(goal))
    asyncio.run(goal_repo.save_key_result(_kr(goal.id, 50.0, 100.0)))   # 50%
    asyncio.run(goal_repo.save_key_result(_kr(goal.id, 100.0, 100.0)))  # 100%

    data = client.get("/dashboard/goal-progress").json()
    item = data["goals"][0]
    assert item["progress_percent"] == 75.0
    assert item["key_results_count"] == 2
    assert item["goal_title"] == "Ship product"
