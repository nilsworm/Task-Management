"""API-level tests for POST/GET/PATCH/DELETE /tasks using TestClient + DI overrides."""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_event_bus, get_task_repo
from src.domain.events import InMemoryEventBus
from src.main import app
from tests.application.conftest import InMemoryTaskRepository


@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def client(task_repo: InMemoryTaskRepository) -> TestClient:
    bus = InMemoryEventBus()
    app.dependency_overrides[get_task_repo] = lambda: task_repo
    app.dependency_overrides[get_event_bus] = lambda: bus
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /tasks
# ---------------------------------------------------------------------------

def test_create_daily_task(client: TestClient) -> None:
    resp = client.post("/tasks", json={
        "task_type": "daily",
        "title": "Write tests",
        "priority": "high",
        "estimation": 3,
        "tags": ["backend"],
        "scheduled_date": "2026-05-01",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_type"] == "daily"
    assert data["title"] == "Write tests"
    assert data["priority"] == "high"
    assert data["estimation"] == 3
    assert data["tags"] == ["backend"]
    assert data["scheduled_date"] == "2026-05-01"
    assert data["status"] == "backlog"
    assert "id" in data


def test_create_sprint_task(client: TestClient) -> None:
    sid = str(uuid.uuid4())
    resp = client.post("/tasks", json={
        "task_type": "sprint",
        "title": "Auth endpoint",
        "sprint_id": sid,
        "estimation": 5,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_type"] == "sprint"
    assert data["sprint_id"] == sid


def test_create_goal_task(client: TestClient) -> None:
    resp = client.post("/tasks", json={
        "task_type": "goal",
        "title": "Learn Rust",
        "date_range_start": "2026-05-01",
        "date_range_end": "2026-07-31",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_type"] == "goal"
    assert data["date_range_start"] == "2026-05-01"
    assert data["date_range_end"] == "2026-07-31"


def test_create_milestone_task(client: TestClient) -> None:
    gid = str(uuid.uuid4())
    resp = client.post("/tasks", json={
        "task_type": "milestone",
        "title": "Ship MVP",
        "due_date": "2026-06-30",
        "goal_id": gid,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_type"] == "milestone"
    assert data["due_date"] == "2026-06-30"
    assert data["goal_id"] == gid


def test_create_task_empty_title_returns_422(client: TestClient) -> None:
    resp = client.post("/tasks", json={"task_type": "daily", "title": ""})
    assert resp.status_code == 422


def test_create_task_unknown_type_returns_422(client: TestClient) -> None:
    resp = client.post("/tasks", json={"task_type": "unknown", "title": "X"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /tasks
# ---------------------------------------------------------------------------

def test_list_tasks_empty(client: TestClient) -> None:
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_returns_all(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Task A"})
    client.post("/tasks", json={"task_type": "daily", "title": "Task B"})
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_tasks_filter_by_status(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Backlog task"})
    task_id = r.json()["id"]
    client.post("/tasks", json={"task_type": "daily", "title": "Another task"})

    # Transition first task to todo
    client.post(f"/tasks/{task_id}/transition", json={"status": "todo"})

    resp = client.get("/tasks?status=todo")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == task_id


def test_list_tasks_filter_by_sprint(client: TestClient) -> None:
    sid = str(uuid.uuid4())
    other_sid = str(uuid.uuid4())
    client.post("/tasks", json={"task_type": "sprint", "title": "In sprint", "sprint_id": sid})
    client.post("/tasks", json={"task_type": "sprint", "title": "Other sprint", "sprint_id": other_sid})

    resp = client.get(f"/tasks?sprint_id={sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sprint_id"] == sid


def test_list_tasks_by_search_returns_matches(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Write documentation"})
    client.post("/tasks", json={"task_type": "daily", "title": "Fix database bug"})

    resp = client.get("/tasks?search=documentation")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Write documentation"


def test_list_tasks_by_search_case_insensitive(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Write Tests"})
    client.post("/tasks", json={"task_type": "daily", "title": "Debug code"})

    resp = client.get("/tasks?search=TESTS")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Write Tests"


def test_list_tasks_by_search_no_matches(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Task A"})
    client.post("/tasks", json={"task_type": "daily", "title": "Task B"})

    resp = client.get("/tasks?search=nonexistent")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 0


def test_list_tasks_by_search_empty_returns_422(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Task"})

    resp = client.get("/tasks?search=")
    assert resp.status_code == 422


def test_list_tasks_overdue_filters_correctly(client: TestClient) -> None:
    # Create overdue task (Milestone with past due_date)
    r1 = client.post("/tasks", json={
        "task_type": "milestone",
        "title": "Overdue task",
        "due_date": "2026-04-01",
    })
    task1_id = r1.json()["id"]
    # Create completed task (should not appear in overdue)
    r2 = client.post("/tasks", json={
        "task_type": "milestone",
        "title": "Done task",
        "due_date": "2026-04-01",
    })
    task2_id = r2.json()["id"]
    # Transition first task to done
    t1 = client.post(f"/tasks/{task1_id}/transition", json={"status": "todo"})
    t1_todo = client.post(f"/tasks/{task1_id}/transition", json={"status": "in_progress"})
    t1_done = client.post(f"/tasks/{task1_id}/transition", json={"status": "review"})
    t1_final = client.post(f"/tasks/{task1_id}/transition", json={"status": "done"})

    # Verify first task is done
    get_task1 = client.get(f"/tasks/{task1_id}")
    assert get_task1.json()["status"] == "done"

    # Leave second task in backlog (not done)

    resp = client.get("/tasks?overdue=true")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Done task"


def test_list_tasks_overdue_false_returns_all(client: TestClient) -> None:
    client.post("/tasks", json={"task_type": "daily", "title": "Task A"})
    client.post("/tasks", json={"task_type": "daily", "title": "Task B"})

    resp = client.get("/tasks?overdue=false")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /tasks/{id}
# ---------------------------------------------------------------------------

def test_get_task_by_id(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Fetch me"})
    task_id = r.json()["id"]

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id
    assert resp.json()["title"] == "Fetch me"


def test_get_task_not_found(client: TestClient) -> None:
    resp = client.get(f"/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /tasks/{id}
# ---------------------------------------------------------------------------

def test_update_task_title(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Old title"})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "New title"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New title"


def test_update_task_priority(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Task", "priority": "low"})
    task_id = r.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"priority": "critical"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "critical"


def test_update_task_not_found(client: TestClient) -> None:
    resp = client.patch(f"/tasks/{uuid.uuid4()}", json={"title": "X"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /tasks/{id}/transition
# ---------------------------------------------------------------------------

def test_transition_task_to_todo(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Task"})
    task_id = r.json()["id"]

    resp = client.post(f"/tasks/{task_id}/transition", json={"status": "todo"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "todo"


def test_transition_task_invalid_returns_409(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Task"})
    task_id = r.json()["id"]

    # backlog → done is not allowed
    resp = client.post(f"/tasks/{task_id}/transition", json={"status": "done"})
    assert resp.status_code == 409


def test_transition_task_not_found(client: TestClient) -> None:
    resp = client.post(f"/tasks/{uuid.uuid4()}/transition", json={"status": "todo"})
    assert resp.status_code == 404


def test_transition_invalid_status_literal_returns_422(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "Task"})
    task_id = r.json()["id"]
    resp = client.post(f"/tasks/{task_id}/transition", json={"status": "flying"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /tasks/{id}
# ---------------------------------------------------------------------------

def test_delete_task(client: TestClient) -> None:
    r = client.post("/tasks", json={"task_type": "daily", "title": "To delete"})
    task_id = r.json()["id"]

    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204

    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_delete_task_not_found(client: TestClient) -> None:
    resp = client.delete(f"/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404
