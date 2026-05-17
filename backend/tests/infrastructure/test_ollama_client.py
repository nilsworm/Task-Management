from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.infrastructure.ai.ollama_client import OllamaClient


@pytest.fixture
def client() -> OllamaClient:
    return OllamaClient(base_url="http://localhost:11434", model="test-model")


@pytest.mark.asyncio
async def test_is_available_returns_true_when_ollama_responds(client: OllamaClient) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await client.is_available()

    assert result is True


@pytest.mark.asyncio
async def test_is_available_returns_false_on_connection_error(client: OllamaClient) -> None:
    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        mock_class.return_value = mock_instance

        result = await client.is_available()

    assert result is False


@pytest.mark.asyncio
async def test_generate_returns_response_text(client: OllamaClient) -> None:
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={"response": "Hallo Welt", "done": True})

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.post = AsyncMock(return_value=mock_response)
        mock_class.return_value = mock_instance

        result = await client.generate(prompt="Test", system="System")

    assert result == "Hallo Welt"


@pytest.mark.asyncio
async def test_generate_stream_yields_tokens(client: OllamaClient) -> None:
    ndjson_lines = [
        json.dumps({"response": "Hal", "done": False}),
        json.dumps({"response": "lo", "done": False}),
        json.dumps({"response": " Welt", "done": True}),
    ]

    async def mock_aiter_lines():
        for line in ndjson_lines:
            yield line

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.aiter_lines = mock_aiter_lines
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_stream_ctx = MagicMock()
    mock_stream_ctx.__aenter__ = AsyncMock(return_value=mock_response)
    mock_stream_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient") as mock_class:
        mock_instance = MagicMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_instance.stream = MagicMock(return_value=mock_stream_ctx)
        mock_class.return_value = mock_instance

        tokens = []
        async for token in client.generate_stream(prompt="Test", system="System"):
            tokens.append(token)

    assert tokens == ["Hal", "lo", " Welt"]
