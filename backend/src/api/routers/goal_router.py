from __future__ import annotations

import uuid

from fastapi import APIRouter

from src.api.dependencies import EventBusDep, GoalRepoDep
from src.api.schemas.goal_schemas import (
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
    KeyResultCreateRequest,
    KeyResultResponse,
    KeyResultUpdateRequest,
)
from src.application.exceptions import EntityNotFoundError
from src.application.use_cases.goal_use_cases import (
    CreateGoalUseCase,
    CreateKeyResultUseCase,
    DeleteGoalUseCase,
    DeleteKeyResultUseCase,
    UpdateGoalUseCase,
    UpdateKeyResultUseCase,
)

router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(body: GoalCreateRequest, repo: GoalRepoDep) -> GoalResponse:
    goal = await CreateGoalUseCase(repo).execute(body.to_domain())
    return GoalResponse.from_domain(goal)


@router.get("", response_model=list[GoalResponse])
async def list_goals(repo: GoalRepoDep) -> list[GoalResponse]:
    goals = await repo.list_all()
    return [GoalResponse.from_domain(g) for g in goals]


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(goal_id: uuid.UUID, repo: GoalRepoDep) -> GoalResponse:
    goal = await repo.get_by_id(goal_id)
    if goal is None:
        raise EntityNotFoundError("Goal", str(goal_id))
    return GoalResponse.from_domain(goal)


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID, body: GoalUpdateRequest, repo: GoalRepoDep
) -> GoalResponse:
    goal = await UpdateGoalUseCase(repo).execute(body.to_use_case_input(goal_id))
    return GoalResponse.from_domain(goal)


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: uuid.UUID, repo: GoalRepoDep, bus: EventBusDep) -> None:
    await DeleteGoalUseCase(repo, bus).execute(goal_id)


# ---------------------------------------------------------------------------
# KeyResults
# ---------------------------------------------------------------------------

@router.get("/{goal_id}/key-results", response_model=list[KeyResultResponse])
async def list_key_results(goal_id: uuid.UUID, repo: GoalRepoDep) -> list[KeyResultResponse]:
    goal = await repo.get_by_id(goal_id)
    if goal is None:
        raise EntityNotFoundError("Goal", str(goal_id))
    krs = await repo.list_key_results(goal_id)
    return [KeyResultResponse.from_domain(kr) for kr in krs]


@router.post("/{goal_id}/key-results", response_model=KeyResultResponse, status_code=201)
async def create_key_result(
    goal_id: uuid.UUID, body: KeyResultCreateRequest, repo: GoalRepoDep
) -> KeyResultResponse:
    kr = await CreateKeyResultUseCase(repo).execute(body.to_use_case_input(goal_id))
    return KeyResultResponse.from_domain(kr)


@router.get("/{goal_id}/key-results/{kr_id}", response_model=KeyResultResponse)
async def get_key_result(
    goal_id: uuid.UUID, kr_id: uuid.UUID, repo: GoalRepoDep
) -> KeyResultResponse:
    kr = await repo.get_key_result(kr_id)
    if kr is None:
        raise EntityNotFoundError("KeyResult", str(kr_id))
    return KeyResultResponse.from_domain(kr)


@router.patch("/{goal_id}/key-results/{kr_id}", response_model=KeyResultResponse)
async def update_key_result(
    goal_id: uuid.UUID,
    kr_id: uuid.UUID,
    body: KeyResultUpdateRequest,
    repo: GoalRepoDep,
) -> KeyResultResponse:
    kr = await UpdateKeyResultUseCase(repo).execute(body.to_use_case_input(kr_id))
    return KeyResultResponse.from_domain(kr)


@router.delete("/{goal_id}/key-results/{kr_id}", status_code=204)
async def delete_key_result(
    goal_id: uuid.UUID, kr_id: uuid.UUID, repo: GoalRepoDep, bus: EventBusDep
) -> None:
    await DeleteKeyResultUseCase(repo, bus).execute(kr_id)
