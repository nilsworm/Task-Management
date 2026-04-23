from __future__ import annotations

from fastapi import APIRouter

from src.api.dependencies import GoalRepoDep, SprintRepoDep, TaskRepoDep
from src.api.schemas.dashboard_schemas import (
    DashboardResponse,
    SprintSummary,
    TaskStatusCounts,
)
from src.application.use_cases.dashboard_use_cases import GetDashboardUseCase

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    task_repo: TaskRepoDep,
    sprint_repo: SprintRepoDep,
    goal_repo: GoalRepoDep,
) -> DashboardResponse:
    data = await GetDashboardUseCase(task_repo, sprint_repo, goal_repo).execute()
    active = (
        SprintSummary(
            id=data.active_sprint.id,
            name=data.active_sprint.name,
            status=data.active_sprint.status,
            total_tasks=data.active_sprint.total_tasks,
            done_tasks=data.active_sprint.done_tasks,
            completion_percent=data.active_sprint.completion_percent,
        )
        if data.active_sprint
        else None
    )
    return DashboardResponse(
        total_tasks=data.total_tasks,
        task_counts=TaskStatusCounts(
            backlog=data.backlog,
            todo=data.todo,
            in_progress=data.in_progress,
            review=data.review,
            blocked=data.blocked,
            done=data.done,
            cancelled=data.cancelled,
        ),
        total_goals=data.total_goals,
        active_sprint=active,
    )
