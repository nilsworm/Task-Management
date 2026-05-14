from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Query

from src.api.dependencies import EventBusDep, TaskRepoDep
from src.application.exceptions import EntityNotFoundError
from src.api.schemas.task_schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskTransitionRequest,
    TaskUpdateRequest,
)
from src.application.use_cases.task_use_cases import (
    CreateTaskUseCase,
    DeleteTaskUseCase,
    TransitionTaskUseCase,
    UpdateTaskUseCase,
)
from src.domain.factory import TaskFactory
from src.domain.value_objects import TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])

_factory = TaskFactory()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    body: TaskCreateRequest,
    repo: TaskRepoDep,
    bus: EventBusDep,
) -> TaskResponse:
    task = await CreateTaskUseCase(repo, _factory, bus).execute(body.to_use_case_input())
    return TaskResponse.from_domain(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    repo: TaskRepoDep,
    status: str | None = Query(None),
    sprint_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None, min_length=1, max_length=200),
) -> list[TaskResponse]:
    if search is not None:
        tasks = await repo.list_by_search(search)
    elif sprint_id is not None:
        tasks = await repo.list_by_sprint(sprint_id)
    elif status is not None:
        tasks = await repo.list_by_status(TaskStatus(status))
    else:
        tasks = await repo.list_all()
    return [TaskResponse.from_domain(t) for t in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: uuid.UUID, repo: TaskRepoDep) -> TaskResponse:
    task = await repo.get_by_id(task_id)
    if task is None:
        raise EntityNotFoundError("Task", str(task_id))
    return TaskResponse.from_domain(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    body: TaskUpdateRequest,
    repo: TaskRepoDep,
    bus: EventBusDep,
) -> TaskResponse:
    task = await UpdateTaskUseCase(repo, bus).execute(body.to_use_case_input(task_id))
    return TaskResponse.from_domain(task)


@router.post("/{task_id}/transition", response_model=TaskResponse)
async def transition_task(
    task_id: uuid.UUID,
    body: TaskTransitionRequest,
    repo: TaskRepoDep,
    bus: EventBusDep,
) -> TaskResponse:
    task = await TransitionTaskUseCase(repo, bus).execute(task_id, body.to_task_status())
    return TaskResponse.from_domain(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: uuid.UUID, repo: TaskRepoDep, bus: EventBusDep) -> None:
    await DeleteTaskUseCase(repo, bus).execute(task_id)
