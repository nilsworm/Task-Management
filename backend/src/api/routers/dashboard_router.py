from __future__ import annotations

from fastapi import APIRouter

from src.api.dependencies import GoalRepoDep, SprintRepoDep, TaskRepoDep
from src.api.schemas.dashboard_schemas import (
    DashboardResponse,
    SprintSummary,
    TaskStatusCounts,
)
from src.domain.value_objects import TaskStatus

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    task_repo: TaskRepoDep,
    sprint_repo: SprintRepoDep,
    goal_repo: GoalRepoDep,
) -> DashboardResponse:
    tasks, goals, active_sprint = await _fetch_all(task_repo, sprint_repo, goal_repo)

    counts = {s: 0 for s in TaskStatus}
    for t in tasks:
        counts[t.status] += 1

    sprint_summary: SprintSummary | None = None
    if active_sprint:
        sprint_tasks = await task_repo.list_by_sprint(active_sprint.id)
        done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
        total = len(sprint_tasks)
        pct = (done / total * 100.0) if total else 0.0
        sprint_summary = SprintSummary(
            id=str(active_sprint.id),
            name=active_sprint.name,
            status=active_sprint.status.value,
            total_tasks=total,
            done_tasks=done,
            completion_percent=round(pct, 1),
        )

    return DashboardResponse(
        total_tasks=len(tasks),
        task_counts=TaskStatusCounts(
            backlog=counts[TaskStatus.BACKLOG],
            todo=counts[TaskStatus.TODO],
            in_progress=counts[TaskStatus.IN_PROGRESS],
            review=counts[TaskStatus.REVIEW],
            blocked=counts[TaskStatus.BLOCKED],
            done=counts[TaskStatus.DONE],
            cancelled=counts[TaskStatus.CANCELLED],
        ),
        total_goals=len(goals),
        active_sprint=sprint_summary,
    )


async def _fetch_all(task_repo, sprint_repo, goal_repo):
    tasks = await task_repo.list_all()
    goals = await goal_repo.list_all()
    active_sprint = await sprint_repo.get_active()
    return tasks, goals, active_sprint
