from __future__ import annotations

import uuid

from fastapi import APIRouter

from src.api.dependencies import EventBusDep, SprintRepoDep, TaskRepoDep
from src.api.schemas.sprint_schemas import SprintCreateRequest, SprintResponse, SprintUpdateRequest
from src.application.exceptions import EntityNotFoundError
from src.application.use_cases.sprint_use_cases import (
    AddTaskToSprintUseCase,
    CompleteSprintUseCase,
    CreateSprintUseCase,
    StartSprintUseCase,
)

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.post("", response_model=SprintResponse, status_code=201)
async def create_sprint(
    body: SprintCreateRequest,
    repo: SprintRepoDep,
    bus: EventBusDep,
) -> SprintResponse:
    sprint = await CreateSprintUseCase(repo, bus).execute(body.name, body.to_date_range())
    return SprintResponse.from_domain(sprint)


@router.get("", response_model=list[SprintResponse])
async def list_sprints(repo: SprintRepoDep) -> list[SprintResponse]:
    sprints = await repo.list_all()
    return [SprintResponse.from_domain(s) for s in sprints]


@router.get("/active", response_model=SprintResponse | None)
async def get_active_sprint(repo: SprintRepoDep) -> SprintResponse | None:
    sprint = await repo.get_active()
    return SprintResponse.from_domain(sprint) if sprint else None


@router.get("/{sprint_id}", response_model=SprintResponse)
async def get_sprint(sprint_id: uuid.UUID, repo: SprintRepoDep) -> SprintResponse:
    sprint = await repo.get_by_id(sprint_id)
    if sprint is None:
        raise EntityNotFoundError("Sprint", str(sprint_id))
    return SprintResponse.from_domain(sprint)


@router.patch("/{sprint_id}", response_model=SprintResponse)
async def update_sprint(
    sprint_id: uuid.UUID,
    body: SprintUpdateRequest,
    repo: SprintRepoDep,
) -> SprintResponse:
    sprint = await repo.get_by_id(sprint_id)
    if sprint is None:
        raise EntityNotFoundError("Sprint", str(sprint_id))
    if body.name is not None:
        sprint.name = body.name
    await repo.save(sprint)
    return SprintResponse.from_domain(sprint)


@router.post("/{sprint_id}/start", response_model=SprintResponse)
async def start_sprint(
    sprint_id: uuid.UUID,
    repo: SprintRepoDep,
    bus: EventBusDep,
) -> SprintResponse:
    sprint = await StartSprintUseCase(repo, bus).execute(sprint_id)
    return SprintResponse.from_domain(sprint)


@router.post("/{sprint_id}/complete", response_model=SprintResponse)
async def complete_sprint(
    sprint_id: uuid.UUID,
    repo: SprintRepoDep,
    bus: EventBusDep,
) -> SprintResponse:
    sprint = await CompleteSprintUseCase(repo, bus).execute(sprint_id)
    return SprintResponse.from_domain(sprint)


@router.post("/{sprint_id}/tasks/{task_id}", response_model=SprintResponse)
async def add_task_to_sprint(
    sprint_id: uuid.UUID,
    task_id: uuid.UUID,
    sprint_repo: SprintRepoDep,
    task_repo: TaskRepoDep,
) -> SprintResponse:
    sprint = await AddTaskToSprintUseCase(sprint_repo, task_repo).execute(sprint_id, task_id)
    return SprintResponse.from_domain(sprint)


@router.delete("/{sprint_id}", status_code=204)
async def delete_sprint(sprint_id: uuid.UUID, repo: SprintRepoDep) -> None:
    sprint = await repo.get_by_id(sprint_id)
    if sprint is None:
        raise EntityNotFoundError("Sprint", str(sprint_id))
    await repo.delete(sprint_id)
