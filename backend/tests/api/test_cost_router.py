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
    # Querying a past month with prior transactions triggers EnsureOpeningBalanceTransactionUseCase,
    # which auto-creates an "Opening Balance April" entry. Filter it out to verify the real transaction.
    user_transactions = [t for t in data if not t["title"].startswith("Opening Balance")]
    assert len(user_transactions) == 1
    assert user_transactions[0]["title"] == "April"


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
# PATCH /cost/recurring/{id}
# ---------------------------------------------------------------------------


def test_patch_recurring_deactivate(client: TestClient) -> None:
    created = client.post(
        "/cost/recurring",
        json={"title": "Netflix", "amount": "17.99", "transaction_type": "expense", "interval": "monthly"},
    )
    rec_id = created.json()["id"]
    resp = client.patch(f"/cost/recurring/{rec_id}", json={"is_active": False})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_patch_recurring_reactivate(client: TestClient) -> None:
    created = client.post(
        "/cost/recurring",
        json={"title": "Strom", "amount": "80.00", "transaction_type": "expense", "interval": "monthly"},
    )
    rec_id = created.json()["id"]
    client.patch(f"/cost/recurring/{rec_id}", json={"is_active": False})
    resp = client.patch(f"/cost/recurring/{rec_id}", json={"is_active": True})
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True


def test_patch_recurring_not_found(client: TestClient) -> None:
    resp = client.patch(f"/cost/recurring/{uuid.uuid4()}", json={"is_active": False})
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


# ---------------------------------------------------------------------------
# POST /cost/import
# ---------------------------------------------------------------------------

CONSORSBANK_CSV = (
    b"Konto\nAllgemeine Informationen\nKontostand\nKontoums\xc3\xa4tze\n"
    b"Buchung;Valuta;Sender / Empf\xc3\xa4nger;IBAN;BIC;Buchungstext;Verwendungszweck;Kategorie;Stichw\xc3\xb6rter;Umsatz geteilt;Betrag;W\xc3\xa4hrung\n"
    b"01.05.2026;01.05.2026;John Doe;DE123;BIC123;UEBERWEISUNG;Salary May;n/a;n/a;n/a;5.000,00;EUR\n"
    b"02.05.2026;02.05.2026;Amazon;DE456;BIC456;KARTENZAHLUNG;Laptop;n/a;n/a;n/a;\xe2\x88\x92250,50;EUR\n"
)

TRADE_REPUBLIC_CSV = (
    b"Datum,Beschreibung,Typ,Betrag\n"
    b"2026-05-01,Dividend Payment,Income,+50.00\n"
    b"2026-05-02,Stock Purchase,Expense,-1200.00\n"
)


def test_import_consorsbank_csv(client: TestClient) -> None:
    """POST /cost/import with valid Consorsbank CSV returns 200 with imported count."""
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


def test_import_trade_republic_csv(client: TestClient) -> None:
    """POST /cost/import with valid Trade Republic CSV returns 200 with imported count."""
    resp = client.post(
        "/cost/import",
        files={"file": ("trade_republic_mai2026.csv", TRADE_REPUBLIC_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0


def test_import_unknown_filename(client: TestClient) -> None:
    """POST /cost/import with unrecognized filename returns 400."""
    resp = client.post(
        "/cost/import",
        files={"file": ("exports.csv", b"Datum,Betrag\n2026-05-01,100", "text/csv")},
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"].lower()
    assert "consorsbank" in detail or "trade_republic" in detail


def test_import_malformed_csv(client: TestClient) -> None:
    """POST /cost/import with wrong columns returns 400."""
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_broken.csv", b"WrongCol1;WrongCol2\n1;2", "text/csv")},
    )
    assert resp.status_code == 400


def test_import_duplicate_skipped(client: TestClient) -> None:
    """Second upload of same CSV results in skipped=2, imported=0."""
    client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    resp = client.post(
        "/cost/import",
        files={"file": ("consorsbank_mai2026.csv", CONSORSBANK_CSV, "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 0
    assert data["skipped"] == 2


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


def test_reset_all_deletes_transactions(client: TestClient) -> None:
    """DELETE /cost/reset wipes all transactions."""
    client.post("/cost/transactions", json={
        "title": "Test", "amount": "100.00",
        "transaction_type": "expense", "date": "2026-05-01",
    })
    resp = client.delete("/cost/reset")
    assert resp.status_code == 204
    assert client.get("/cost/transactions").json() == []


def test_reset_all_deletes_recurring(client: TestClient) -> None:
    """DELETE /cost/reset wipes all recurring entries."""
    client.post("/cost/recurring", json={
        "title": "Netflix", "amount": "15.00",
        "transaction_type": "expense", "day_of_month": 1,
    })
    client.delete("/cost/reset")
    assert client.get("/cost/recurring").json() == []

