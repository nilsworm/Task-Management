from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import (
    entity_not_found_handler,
    invalid_operation_handler,
    value_error_handler,
)
from src.api.health import router as health_router
from src.api.routers.cost_router import router as cost_router
from src.api.routers.dashboard_router import router as dashboard_router
from src.api.routers.goal_router import router as goal_router
from src.api.routers.sprint_router import router as sprint_router
from src.api.routers.task_router import router as task_router
from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.config import settings

app = FastAPI(
    title="Task Manager API",
    version="0.1.0",
    description="Personal task management — single-user, local-only.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(EntityNotFoundError, entity_not_found_handler)  # type: ignore[arg-type]
app.add_exception_handler(InvalidOperationError, invalid_operation_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]

app.include_router(health_router)
app.include_router(task_router)
app.include_router(sprint_router)
app.include_router(goal_router)
app.include_router(dashboard_router)
app.include_router(cost_router)
