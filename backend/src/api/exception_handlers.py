from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from src.application.exceptions import EntityNotFoundError, InvalidOperationError


async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


async def invalid_operation_handler(request: Request, exc: InvalidOperationError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})
