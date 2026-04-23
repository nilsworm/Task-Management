"""Verify that domain exceptions are mapped to the correct HTTP status codes."""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRouter
from httpx import ASGITransport, AsyncClient

from src.api.exception_handlers import (
    entity_not_found_handler,
    invalid_operation_handler,
    value_error_handler,
)
from src.application.exceptions import EntityNotFoundError, InvalidOperationError


def _make_app() -> FastAPI:
    """Minimal FastAPI app with the three exception handlers and test routes."""
    app = FastAPI()
    app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)  # type: ignore[arg-type]
    app.add_exception_handler(InvalidOperationError, invalid_operation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]

    router = APIRouter()

    @router.get("/raise/not-found")
    async def _not_found() -> None:
        raise EntityNotFoundError("Task", "abc-123")

    @router.get("/raise/conflict")
    async def _conflict() -> None:
        raise InvalidOperationError("Cannot transition from DONE to TODO")

    @router.get("/raise/bad-request")
    async def _bad_request() -> None:
        raise ValueError("Unknown task_type: 'bogus'")

    app.include_router(router)
    return app


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=_make_app()), base_url="http://test"
    ) as c:
        yield c


async def test_entity_not_found_returns_404(client: AsyncClient) -> None:
    response = await client.get("/raise/not-found")
    assert response.status_code == 404
    assert "Task abc-123 not found" in response.json()["detail"]


async def test_invalid_operation_returns_409(client: AsyncClient) -> None:
    response = await client.get("/raise/conflict")
    assert response.status_code == 409
    assert "Cannot transition" in response.json()["detail"]


async def test_value_error_returns_400(client: AsyncClient) -> None:
    response = await client.get("/raise/bad-request")
    assert response.status_code == 400
    assert "bogus" in response.json()["detail"]


async def test_entity_not_found_is_subclass_of_value_error() -> None:
    exc = EntityNotFoundError("Sprint", "xyz")
    assert isinstance(exc, ValueError)
    assert "Sprint xyz not found" in str(exc)


async def test_invalid_operation_is_subclass_of_value_error() -> None:
    exc = InvalidOperationError("bad state")
    assert isinstance(exc, ValueError)
