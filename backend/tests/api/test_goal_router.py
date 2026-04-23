"""API-level tests for /goals router using TestClient + DI overrides."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_goal_repo
from src.main import app
from tests.application.conftest import InMemoryGoalRepository


@pytest.fixture
def goal_repo() -> InMemoryGoalRepository:
    return InMemoryGoalRepository()


@pytest.fixture
def client(goal_repo: InMemoryGoalRepository) -> TestClient:
    app.dependency_overrides[get_goal_repo] = lambda: goal_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _create_goal(client: TestClient, title: str = "Master FastAPI") -> dict:
    resp = client.post("/goals", json={"title": title})
    assert resp.status_code == 201
    return resp.json()


# ---------------------------------------------------------------------------
# POST /goals
# ---------------------------------------------------------------------------

def test_create_goal_minimal(client: TestClient) -> None:
    data = _create_goal(client)
    assert data["title"] == "Master FastAPI"
    assert data["status"] == "backlog"
    assert data["priority"] == "medium"
    assert data["tags"] == []
    assert "id" in data


def test_create_goal_full(client: TestClient) -> None:
    resp = client.post("/goals", json={
        "title": "Learn Rust",
        "description": "Systems programming",
        "priority": "high",
        "tags": ["rust", "systems"],
        "date_range_start": "2026-05-01",
        "date_range_end": "2026-07-31",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["description"] == "Systems programming"
    assert data["priority"] == "high"
    assert data["tags"] == ["rust", "systems"]
    assert data["date_range_start"] == "2026-05-01"
    assert data["date_range_end"] == "2026-07-31"


def test_create_goal_empty_title_returns_422(client: TestClient) -> None:
    assert client.post("/goals", json={"title": ""}).status_code == 422


# ---------------------------------------------------------------------------
# GET /goals
# ---------------------------------------------------------------------------

def test_list_goals_empty(client: TestClient) -> None:
    assert client.get("/goals").json() == []


def test_list_goals_returns_all(client: TestClient) -> None:
    _create_goal(client, "Goal A")
    _create_goal(client, "Goal B")
    assert len(client.get("/goals").json()) == 2


# ---------------------------------------------------------------------------
# GET /goals/{id}
# ---------------------------------------------------------------------------

def test_get_goal_by_id(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.get(f"/goals/{goal['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == goal["id"]


def test_get_goal_not_found(client: TestClient) -> None:
    assert client.get(f"/goals/{uuid.uuid4()}").status_code == 404


# ---------------------------------------------------------------------------
# PATCH /goals/{id}
# ---------------------------------------------------------------------------

def test_update_goal_title(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.patch(f"/goals/{goal['id']}", json={"title": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated"


def test_update_goal_priority(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.patch(f"/goals/{goal['id']}", json={"priority": "critical"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "critical"


def test_update_goal_tags(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.patch(f"/goals/{goal['id']}", json={"tags": ["alpha", "beta"]})
    assert resp.status_code == 200
    assert sorted(resp.json()["tags"]) == ["alpha", "beta"]


def test_update_goal_not_found(client: TestClient) -> None:
    assert client.patch(f"/goals/{uuid.uuid4()}", json={"title": "X"}).status_code == 404


# ---------------------------------------------------------------------------
# DELETE /goals/{id}
# ---------------------------------------------------------------------------

def test_delete_goal(client: TestClient) -> None:
    goal = _create_goal(client)
    assert client.delete(f"/goals/{goal['id']}").status_code == 204
    assert client.get(f"/goals/{goal['id']}").status_code == 404


def test_delete_goal_not_found(client: TestClient) -> None:
    assert client.delete(f"/goals/{uuid.uuid4()}").status_code == 404


# ---------------------------------------------------------------------------
# POST /goals/{id}/key-results
# ---------------------------------------------------------------------------

def test_create_key_result(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/key-results", json={
        "title": "Ship 10 features",
        "target_value": 10.0,
        "unit": "features",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Ship 10 features"
    assert data["target_value"] == 10.0
    assert data["current_value"] == 0.0
    assert data["progress_percent"] == 0.0
    assert data["goal_id"] == goal["id"]


def test_create_key_result_goal_not_found(client: TestClient) -> None:
    resp = client.post(f"/goals/{uuid.uuid4()}/key-results", json={
        "title": "KR", "target_value": 5.0
    })
    assert resp.status_code == 404


def test_create_key_result_zero_target_returns_422(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.post(f"/goals/{goal['id']}/key-results", json={
        "title": "KR", "target_value": 0.0
    })
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /goals/{id}/key-results
# ---------------------------------------------------------------------------

def test_list_key_results_empty(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.get(f"/goals/{goal['id']}/key-results")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_key_results(client: TestClient) -> None:
    goal = _create_goal(client)
    client.post(f"/goals/{goal['id']}/key-results", json={"title": "KR 1", "target_value": 5.0})
    client.post(f"/goals/{goal['id']}/key-results", json={"title": "KR 2", "target_value": 10.0})
    data = client.get(f"/goals/{goal['id']}/key-results").json()
    assert len(data) == 2


def test_list_key_results_goal_not_found(client: TestClient) -> None:
    assert client.get(f"/goals/{uuid.uuid4()}/key-results").status_code == 404


# ---------------------------------------------------------------------------
# PATCH /goals/{id}/key-results/{kr_id}
# ---------------------------------------------------------------------------

def test_update_key_result_progress(client: TestClient) -> None:
    goal = _create_goal(client)
    kr = client.post(f"/goals/{goal['id']}/key-results", json={
        "title": "KR", "target_value": 10.0
    }).json()

    resp = client.patch(f"/goals/{goal['id']}/key-results/{kr['id']}", json={"current_value": 5.0})
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_value"] == 5.0
    assert data["progress_percent"] == 50.0


def test_update_key_result_not_found(client: TestClient) -> None:
    goal = _create_goal(client)
    resp = client.patch(f"/goals/{goal['id']}/key-results/{uuid.uuid4()}", json={"current_value": 1.0})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /goals/{id}/key-results/{kr_id}
# ---------------------------------------------------------------------------

def test_delete_key_result(client: TestClient) -> None:
    goal = _create_goal(client)
    kr = client.post(f"/goals/{goal['id']}/key-results", json={
        "title": "KR", "target_value": 5.0
    }).json()

    assert client.delete(f"/goals/{goal['id']}/key-results/{kr['id']}").status_code == 204
    assert client.get(f"/goals/{goal['id']}/key-results").json() == []


def test_delete_key_result_not_found(client: TestClient) -> None:
    goal = _create_goal(client)
    assert client.delete(f"/goals/{goal['id']}/key-results/{uuid.uuid4()}").status_code == 404
