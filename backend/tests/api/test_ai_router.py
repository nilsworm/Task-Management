from __future__ import annotations

from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from src.api.dependencies import get_ai_advisor_service
from src.application.services.ai_advisor import AIAdvisorService, InsightCard
from src.main import app


class MockAIAdvisorService:
    def __init__(
        self,
        insights: list[InsightCard] | None = None,
        stream_tokens: list[str] | None = None,
    ) -> None:
        self._insights = insights or [
            InsightCard(title="Test Insight", body="Test body", type="tip"),
        ]
        self._stream_tokens = stream_tokens or ["Hallo ", "Welt"]

    async def get_insights(self) -> list[InsightCard]:
        return self._insights

    async def stream_chat(self, message: str, history: list[dict[str, str]] | None = None) -> AsyncIterator[str]:
        for token in self._stream_tokens:
            yield token


@pytest.fixture
def mock_service() -> MockAIAdvisorService:
    return MockAIAdvisorService()


@pytest.fixture
def client(mock_service: MockAIAdvisorService) -> TestClient:
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /ai/insights
# ---------------------------------------------------------------------------


def test_insights_returns_200_with_cards(client: TestClient) -> None:
    resp = client.post("/ai/insights")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Test Insight"
    assert data[0]["body"] == "Test body"
    assert data[0]["type"] == "tip"


def test_insights_returns_503_when_service_unavailable(mock_service: MockAIAdvisorService) -> None:
    async def raise_503():
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Ollama not available")

    mock_service.get_insights = raise_503  # type: ignore[assignment]
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        resp = c.post("/ai/insights")
    app.dependency_overrides.clear()
    assert resp.status_code == 503


def test_insights_returns_503_when_ollama_unreachable(mock_service: MockAIAdvisorService) -> None:
    async def raise_connect_error():
        raise ConnectionError("Ollama not reachable")

    mock_service.get_insights = raise_connect_error  # type: ignore[assignment]
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        resp = c.post("/ai/insights")
    app.dependency_overrides.clear()
    assert resp.status_code == 503


# ---------------------------------------------------------------------------
# POST /ai/chat
# ---------------------------------------------------------------------------


def test_chat_returns_200_sse_stream(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": "Was sind meine größten Ausgaben?"})
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    body = resp.text
    assert "data: Hallo \n\n" in body
    assert "data: [DONE]\n\n" in body


def test_chat_returns_422_for_empty_message(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": ""})
    assert resp.status_code == 422


def test_chat_returns_422_for_message_too_long(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={"message": "x" * 501})
    assert resp.status_code == 422


def test_chat_sends_history(client: TestClient) -> None:
    resp = client.post("/ai/chat", json={
        "message": "Und im April?",
        "history": [
            {"role": "user", "content": "Was kostet mich Tabak?"},
            {"role": "assistant", "content": "Im Mai 12€."},
        ],
    })
    assert resp.status_code == 200
    assert "data: [DONE]\n\n" in resp.text


def test_chat_returns_503_when_service_unavailable(mock_service: MockAIAdvisorService) -> None:
    async def raise_connection_error(message: str, history: list | None = None) -> AsyncIterator[str]:
        raise ConnectionError("Ollama not reachable")
        yield  # makes it an async generator

    mock_service.stream_chat = raise_connection_error  # type: ignore[assignment]
    app.dependency_overrides[get_ai_advisor_service] = lambda: mock_service
    with TestClient(app) as c:
        resp = c.post("/ai/chat", json={"message": "test"})
    app.dependency_overrides.clear()
    assert resp.status_code == 503
