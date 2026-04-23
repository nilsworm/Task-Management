"""API-level tests for /sprints router using TestClient + DI overrides."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_event_bus, get_sprint_repo, get_task_repo
from src.domain.events import InMemoryEventBus
from src.main import app
from tests.application.conftest import InMemorySprintRepository, InMemoryTaskRepository


@pytest.fixture
def sprint_repo() -> InMemorySprintRepository:
    return InMemorySprintRepository()


@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def client(sprint_repo: InMemorySprintRepository, task_repo: InMemoryTaskRepository) -> TestClient:
    bus = InMemoryEventBus()
    app.dependency_overrides[get_sprint_repo] = lambda: sprint_repo
    app.dependency_overrides[get_task_repo] = lambda: task_repo
    app.dependency_overrides[get_event_bus] = lambda: bus
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_sprint(client: TestClient, name: str = "Sprint 1") -> dict:
    resp = client.post("/sprints", json={
        "name": name,
        "start_date": "2026-05-01",
        "end_date": "2026-05-14",
    })
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /sprints
# ---------------------------------------------------------------------------

def test_create_sprint(client: TestClient) -> None:
    data = _create_sprint(client)
    assert data["name"] == "Sprint 1"
    assert data["status"] == "planned"
    assert data["start_date"] == "2026-05-01"
    assert data["end_date"] == "2026-05-14"
    assert "id" in data


def test_create_sprint_invalid_date_range_returns_400(client: TestClient) -> None:
    resp = client.post("/sprints", json={
        "name": "Bad Sprint",
        "start_date": "2026-05-14",
        "end_date": "2026-05-01",
    })
    assert resp.status_code == 400


def test_create_sprint_empty_name_returns_422(client: TestClient) -> None:
    resp = client.post("/sprints", json={
        "name": "",
        "start_date": "2026-05-01",
        "end_date": "2026-05-14",
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /sprints
# ---------------------------------------------------------------------------

def test_list_sprints_empty(client: TestClient) -> None:
    assert client.get("/sprints").json() == []


def test_list_sprints_returns_all(client: TestClient) -> None:
    _create_sprint(client, "Sprint A")
    _create_sprint(client, "Sprint B")
    data = client.get("/sprints").json()
    assert len(data) == 2


# ---------------------------------------------------------------------------
# GET /sprints/active
# ---------------------------------------------------------------------------

def test_get_active_sprint_none(client: TestClient) -> None:
    resp = client.get("/sprints/active")
    assert resp.status_code == 200
    assert resp.json() is None


def test_get_active_sprint(client: TestClient) -> None:
    sprint = _create_sprint(client)
    client.post(f"/sprints/{sprint['id']}/start")

    resp = client.get("/sprints/active")
    assert resp.status_code == 200
    assert resp.json()["id"] == sprint["id"]
    assert resp.json()["status"] == "active"


# ---------------------------------------------------------------------------
# GET /sprints/{id}
# ---------------------------------------------------------------------------

def test_get_sprint_by_id(client: TestClient) -> None:
    sprint = _create_sprint(client)
    resp = client.get(f"/sprints/{sprint['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == sprint["id"]


def test_get_sprint_not_found(client: TestClient) -> None:
    resp = client.get(f"/sprints/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /sprints/{id}
# ---------------------------------------------------------------------------

def test_update_sprint_name(client: TestClient) -> None:
    sprint = _create_sprint(client)
    resp = client.patch(f"/sprints/{sprint['id']}", json={"name": "Renamed Sprint"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Sprint"


def test_update_sprint_not_found(client: TestClient) -> None:
    resp = client.patch(f"/sprints/{uuid.uuid4()}", json={"name": "X"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /sprints/{id}/start
# ---------------------------------------------------------------------------

def test_start_sprint(client: TestClient) -> None:
    sprint = _create_sprint(client)
    resp = client.post(f"/sprints/{sprint['id']}/start")
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


def test_start_already_active_sprint_returns_409(client: TestClient) -> None:
    sprint = _create_sprint(client)
    client.post(f"/sprints/{sprint['id']}/start")
    resp = client.post(f"/sprints/{sprint['id']}/start")
    assert resp.status_code == 409


def test_start_sprint_not_found(client: TestClient) -> None:
    resp = client.post(f"/sprints/{uuid.uuid4()}/start")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /sprints/{id}/complete
# ---------------------------------------------------------------------------

def test_complete_sprint(client: TestClient) -> None:
    sprint = _create_sprint(client)
    client.post(f"/sprints/{sprint['id']}/start")
    resp = client.post(f"/sprints/{sprint['id']}/complete")
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


def test_complete_planned_sprint_returns_409(client: TestClient) -> None:
    sprint = _create_sprint(client)
    resp = client.post(f"/sprints/{sprint['id']}/complete")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /sprints/{id}/tasks/{task_id}
# ---------------------------------------------------------------------------

def test_add_task_to_sprint(client: TestClient, task_repo: InMemoryTaskRepository) -> None:
    from src.domain.factory import TaskFactory
    from src.domain.value_objects import Priority

    factory = TaskFactory()
    sprint_data = _create_sprint(client)
    sprint_id = uuid.UUID(sprint_data["id"])

    task = factory.create_sprint("Auth endpoint", sprint_id=sprint_id)
    import asyncio
    asyncio.run(task_repo.save(task))

    resp = client.post(f"/sprints/{sprint_id}/tasks/{task.id}")
    assert resp.status_code == 200
    assert str(task.id) in resp.json()["task_ids"]


def test_add_task_sprint_not_found(client: TestClient) -> None:
    resp = client.post(f"/sprints/{uuid.uuid4()}/tasks/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /sprints/{id}
# ---------------------------------------------------------------------------

def test_delete_sprint(client: TestClient) -> None:
    sprint = _create_sprint(client)
    resp = client.delete(f"/sprints/{sprint['id']}")
    assert resp.status_code == 204
    assert client.get(f"/sprints/{sprint['id']}").status_code == 404


def test_delete_sprint_not_found(client: TestClient) -> None:
    resp = client.delete(f"/sprints/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_delete_active_sprint_returns_409(client: TestClient) -> None:
    sprint = _create_sprint(client)
    client.post(f"/sprints/{sprint['id']}/start")
    resp = client.delete(f"/sprints/{sprint['id']}")
    assert resp.status_code == 409


def test_update_sprint_name_via_use_case(client: TestClient) -> None:
    sprint = _create_sprint(client, "Original")
    resp = client.patch(f"/sprints/{sprint['id']}", json={"name": "Renamed"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"
