"""API-level tests for /cost endpoints using TestClient + DI overrides."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_cost_repo
from src.domain.cost.entities import RecurringTransaction, Transaction
from src.domain.cost.repository import ICostRepository
from src.domain.cost.value_objects import RecurrenceInterval, TransactionType
from src.main import app
from tests.application.test_cost_use_cases import InMemoryCostRepository


@pytest.fixture
def repo() -> InMemoryCostRepository:
    return InMemoryCostRepository()


@pytest.fixture
def client(repo: InMemoryCostRepository) -> TestClient:
    app.dependency_overrides[get_cost_repo] = lambda: repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /cost/transactions
# ---------------------------------------------------------------------------


def test_create_transaction_201(client: TestClient) -> None:
    resp = client.post(
        "/cost/transactions",
        json={
            "title": "Miete",
            "amount": "800.00",
            "transaction_type": "expense",
            "date": "2026-04-01",
            "tags": ["Miete"],
            "description": "Monatliche Miete",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Miete"
    assert data["transaction_type"] == "expense"
    assert data["tags"] == ["miete"]  # normalized
    assert "id" in data


def test_create_transaction_invalid_amount(client: TestClient) -> None:
    resp = client.post(
        "/cost/transactions",
        json={
            "title": "Test",
            "amount": "0",
            "transaction_type": "expense",
            "date": "2026-04-01",
        },
    )
    assert resp.status_code == 422


def test_create_transaction_invalid_type(client: TestClient) -> None:
    resp = client.post(
        "/cost/transactions",
        json={
            "title": "Test",
            "amount": "10.00",
            "transaction_type": "invalid",
            "date": "2026-04-01",
        },
    )
    assert resp.status_code == 422


def test_create_transaction_empty_title(client: TestClient) -> None:
    resp = client.post(
        "/cost/transactions",
        json={
            "title": "",
            "amount": "10.00",
            "transaction_type": "expense",
            "date": "2026-04-01",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /cost/transactions
# ---------------------------------------------------------------------------


def test_list_transactions_empty(client: TestClient) -> None:
    resp = client.get("/cost/transactions")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_transactions_returns_created(client: TestClient) -> None:
    client.post(
        "/cost/transactions",
        json={
            "title": "Gehalt",
            "amount": "3000.00",
            "transaction_type": "income",
            "date": str(date.today()),
        },
    )
    resp = client.get("/cost/transactions")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_transactions_filter_month(client: TestClient) -> None:
    client.post(
        "/cost/transactions",
        json={"title": "April", "amount": "10.00", "transaction_type": "expense", "date": "2026-04-01"},
    )
    client.post(
        "/cost/transactions",
        json={"title": "March", "amount": "10.00", "transaction_type": "expense", "date": "2026-03-01"},
    )
    resp = client.get("/cost/transactions?year=2026&month=4")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "April"


# ---------------------------------------------------------------------------
# DELETE /cost/transactions/{id}
# ---------------------------------------------------------------------------


def test_delete_transaction_current_month(client: TestClient, repo: InMemoryCostRepository) -> None:
    created = client.post(
        "/cost/transactions",
        json={
            "title": "Test",
            "amount": "10.00",
            "transaction_type": "expense",
            "date": str(date.today()),
        },
    )
    tx_id = created.json()["id"]
    resp = client.delete(f"/cost/transactions/{tx_id}")
    assert resp.status_code == 204


def test_delete_transaction_past_month_rejected(client: TestClient) -> None:
    created = client.post(
        "/cost/transactions",
        json={
            "title": "Old",
            "amount": "10.00",
            "transaction_type": "expense",
            "date": "2025-01-01",
        },
    )
    tx_id = created.json()["id"]
    resp = client.delete(f"/cost/transactions/{tx_id}")
    assert resp.status_code == 409


def test_delete_transaction_not_found(client: TestClient) -> None:
    resp = client.delete(f"/cost/transactions/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /cost/recurring
# ---------------------------------------------------------------------------


def test_create_recurring_201(client: TestClient) -> None:
    resp = client.post(
        "/cost/recurring",
        json={
            "title": "Netflix",
            "amount": "17.99",
            "transaction_type": "expense",
            "interval": "monthly",
            "day_of_month": 15,
            "tags": ["Freizeit"],
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Netflix"
    assert data["interval"] == "monthly"
    assert data["is_active"] is True
    assert data["tags"] == ["freizeit"]


def test_create_recurring_invalid_day_of_month(client: TestClient) -> None:
    resp = client.post(
        "/cost/recurring",
        json={
            "title": "Test",
            "amount": "10.00",
            "transaction_type": "expense",
            "interval": "monthly",
            "day_of_month": 29,
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /cost/recurring
# ---------------------------------------------------------------------------


def test_list_recurring_empty(client: TestClient) -> None:
    resp = client.get("/cost/recurring")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_recurring_returns_created(client: TestClient) -> None:
    client.post(
        "/cost/recurring",
        json={"title": "Miete", "amount": "800.00", "transaction_type": "expense", "interval": "monthly"},
    )
    resp = client.get("/cost/recurring")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


# ---------------------------------------------------------------------------
# DELETE /cost/recurring/{id}
# ---------------------------------------------------------------------------


def test_delete_recurring_success(client: TestClient) -> None:
    created = client.post(
        "/cost/recurring",
        json={"title": "Strom", "amount": "80.00", "transaction_type": "expense", "interval": "monthly"},
    )
    rec_id = created.json()["id"]
    resp = client.delete(f"/cost/recurring/{rec_id}")
    assert resp.status_code == 204


def test_delete_recurring_not_found(client: TestClient) -> None:
    resp = client.delete(f"/cost/recurring/{uuid.uuid4()}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /cost/generate-monthly
# ---------------------------------------------------------------------------


def test_generate_monthly_requires_params(client: TestClient) -> None:
    resp = client.post("/cost/generate-monthly")
    assert resp.status_code == 422


def test_generate_monthly_no_recurring_returns_empty(client: TestClient) -> None:
    resp = client.post("/cost/generate-monthly?year=2026&month=5")
    assert resp.status_code == 201
    assert resp.json() == []


def test_generate_monthly_creates_transactions(client: TestClient) -> None:
    client.post("/cost/recurring", json={
        "title": "Miete", "amount": "800.00",
        "transaction_type": "expense", "interval": "monthly", "day_of_month": 1,
    })
    resp = client.post("/cost/generate-monthly?year=2026&month=5")
    assert resp.status_code == 201
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "Miete"
    assert data[0]["date"] == "2026-05-01"


def test_generate_monthly_409_on_duplicate(client: TestClient) -> None:
    client.post("/cost/recurring", json={
        "title": "Miete", "amount": "800.00",
        "transaction_type": "expense", "interval": "monthly",
    })
    client.post("/cost/generate-monthly?year=2026&month=5")
    resp = client.post("/cost/generate-monthly?year=2026&month=5")
    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# GET /cost/summary
# ---------------------------------------------------------------------------


def test_summary_requires_year_and_month(client: TestClient) -> None:
    resp = client.get("/cost/summary")
    assert resp.status_code == 422


def test_summary_empty_month(client: TestClient) -> None:
    resp = client.get("/cost/summary?year=2026&month=4")
    assert resp.status_code == 200
    data = resp.json()
    assert data["income"] == "0"
    assert data["expenses"] == "0"
    assert data["balance"] == "0"


def test_summary_calculates_correctly(client: TestClient) -> None:
    today = str(date.today())
    now = date.today()
    client.post("/cost/transactions", json={
        "title": "Gehalt", "amount": "3000.00", "transaction_type": "income", "date": today,
    })
    client.post("/cost/transactions", json={
        "title": "Miete", "amount": "800.00", "transaction_type": "expense", "date": today,
    })
    resp = client.get(f"/cost/summary?year={now.year}&month={now.month}")
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["income"]) == Decimal("3000.00")
    assert Decimal(data["expenses"]) == Decimal("800.00")
    assert Decimal(data["balance"]) == Decimal("2200.00")


# ---------------------------------------------------------------------------
# GET /cost/tags
# ---------------------------------------------------------------------------


def test_list_tags_combines_all_sources(client: TestClient) -> None:
    client.post(
        "/cost/transactions",
        json={"title": "Einkauf", "amount": "50.00", "transaction_type": "expense",
              "date": str(date.today()), "tags": ["lebensmittel"]},
    )
    client.post(
        "/cost/recurring",
        json={"title": "Strom", "amount": "80.00", "transaction_type": "expense",
              "interval": "monthly", "tags": ["versicherung"]},
    )
    resp = client.get("/cost/tags")
    assert resp.status_code == 200
    tags = resp.json()
    assert "lebensmittel" in tags
    assert "versicherung" in tags


# ---------------------------------------------------------------------------
# GET /cost/analytics
# ---------------------------------------------------------------------------


def test_analytics_requires_year_and_month(client: TestClient) -> None:
    resp = client.get("/cost/analytics")
    assert resp.status_code == 422


def test_analytics_empty_returns_structure(client: TestClient) -> None:
    resp = client.get("/cost/analytics?year=2026&month=4")
    assert resp.status_code == 200
    data = resp.json()
    assert "expenses_by_tag" in data
    assert "monthly_comparison" in data
    assert len(data["monthly_comparison"]) == 6


def test_analytics_expenses_by_tag(client: TestClient) -> None:
    today = str(date.today())
    now = date.today()
    client.post("/cost/transactions", json={
        "title": "Einkauf", "amount": "120.00", "transaction_type": "expense",
        "date": today, "tags": ["lebensmittel"],
    })
    client.post("/cost/transactions", json={
        "title": "Benzin", "amount": "60.00", "transaction_type": "expense",
        "date": today, "tags": ["transport"],
    })
    resp = client.get(f"/cost/analytics?year={now.year}&month={now.month}")
    assert resp.status_code == 200
    by_tag = {item["tag"]: Decimal(item["amount"]) for item in resp.json()["expenses_by_tag"]}
    assert by_tag["lebensmittel"] == Decimal("120.00")
    assert by_tag["transport"] == Decimal("60.00")


def test_analytics_income_not_in_by_tag(client: TestClient) -> None:
    today = str(date.today())
    now = date.today()
    client.post("/cost/transactions", json={
        "title": "Gehalt", "amount": "3000.00", "transaction_type": "income",
        "date": today, "tags": ["gehalt"],
    })
    resp = client.get(f"/cost/analytics?year={now.year}&month={now.month}")
    assert resp.status_code == 200
    tags = [item["tag"] for item in resp.json()["expenses_by_tag"]]
    assert "gehalt" not in tags
