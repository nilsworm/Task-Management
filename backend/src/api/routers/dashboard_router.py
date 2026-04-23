from __future__ import annotations

import uuid

from fastapi import APIRouter, Query

from src.api.dependencies import GoalRepoDep, SprintRepoDep, TaskRepoDep
from src.api.schemas.dashboard_schemas import (
    BurndownPoint,
    BurndownResponse,
    DashboardResponse,
    GoalProgressItem,
    GoalProgressResponse,
    MetricsResponse,
    SprintSummary,
    SprintVelocity,
    TaskStatusCounts,
    VelocityResponse,
)
from src.application.use_cases.dashboard_use_cases import (
    GetDashboardMetricsUseCase,
    GetDashboardUseCase,
    GetGoalProgressUseCase,
    GetSprintBurndownUseCase,
    GetVelocityUseCase,
)

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


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(task_repo: TaskRepoDep) -> MetricsResponse:
    data = await GetDashboardMetricsUseCase(task_repo).execute()
    return MetricsResponse(
        task_counts=TaskStatusCounts(
            backlog=data.backlog,
            todo=data.todo,
            in_progress=data.in_progress,
            review=data.review,
            blocked=data.blocked,
            done=data.done,
            cancelled=data.cancelled,
        ),
        completion_rate=data.completion_rate,
    )


@router.get("/burndown", response_model=BurndownResponse)
async def get_burndown(
    task_repo: TaskRepoDep,
    sprint_repo: SprintRepoDep,
    sprint_id: uuid.UUID | None = Query(None),
) -> BurndownResponse:
    data = await GetSprintBurndownUseCase(task_repo, sprint_repo).execute(sprint_id)
    return BurndownResponse(
        sprint_id=data.sprint_id,
        sprint_name=data.sprint_name,
        start_date=data.start_date,
        end_date=data.end_date,
        total_points=data.total_points,
        ideal_line=[BurndownPoint(date=p.date, remaining_points=p.remaining_points) for p in data.ideal_line],
        actual_remaining=data.actual_remaining,
    )


@router.get("/velocity", response_model=VelocityResponse)
async def get_velocity(
    task_repo: TaskRepoDep,
    sprint_repo: SprintRepoDep,
    last_n: int = Query(5, ge=1),
) -> VelocityResponse:
    data = await GetVelocityUseCase(task_repo, sprint_repo).execute(last_n)
    return VelocityResponse(
        sprints=[
            SprintVelocity(
                sprint_id=s.sprint_id,
                sprint_name=s.sprint_name,
                completed_points=s.completed_points,
            )
            for s in data.sprints
        ],
        average_velocity=data.average_velocity,
    )


@router.get("/goal-progress", response_model=GoalProgressResponse)
async def get_goal_progress(goal_repo: GoalRepoDep) -> GoalProgressResponse:
    data = await GetGoalProgressUseCase(goal_repo).execute()
    return GoalProgressResponse(
        goals=[
            GoalProgressItem(
                goal_id=g.goal_id,
                goal_title=g.goal_title,
                progress_percent=g.progress_percent,
                key_results_count=g.key_results_count,
            )
            for g in data.goals
        ]
    )
