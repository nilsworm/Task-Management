from __future__ import annotations

from dataclasses import dataclass

from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.value_objects import TaskStatus


@dataclass
class SprintSummaryData:
    id: str
    name: str
    status: str
    total_tasks: int
    done_tasks: int
    completion_percent: float


@dataclass
class DashboardData:
    total_tasks: int
    backlog: int
    todo: int
    in_progress: int
    review: int
    blocked: int
    done: int
    cancelled: int
    total_goals: int
    active_sprint: SprintSummaryData | None


class GetDashboardUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        sprint_repo: ISprintRepository,
        goal_repo: IGoalRepository,
    ) -> None:
        self._task_repo = task_repo
        self._sprint_repo = sprint_repo
        self._goal_repo = goal_repo

    async def execute(self) -> DashboardData:
        tasks = await self._task_repo.list_all()
        goals = await self._goal_repo.list_all()
        active_sprint = await self._sprint_repo.get_active()

        counts = {s: 0 for s in TaskStatus}
        for t in tasks:
            counts[t.status] += 1

        sprint_summary: SprintSummaryData | None = None
        if active_sprint:
            sprint_tasks = await self._task_repo.list_by_sprint(active_sprint.id)
            done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
            total = len(sprint_tasks)
            pct = round((done / total * 100.0) if total else 0.0, 1)
            sprint_summary = SprintSummaryData(
                id=str(active_sprint.id),
                name=active_sprint.name,
                status=active_sprint.status.value,
                total_tasks=total,
                done_tasks=done,
                completion_percent=pct,
            )

        return DashboardData(
            total_tasks=len(tasks),
            backlog=counts[TaskStatus.BACKLOG],
            todo=counts[TaskStatus.TODO],
            in_progress=counts[TaskStatus.IN_PROGRESS],
            review=counts[TaskStatus.REVIEW],
            blocked=counts[TaskStatus.BLOCKED],
            done=counts[TaskStatus.DONE],
            cancelled=counts[TaskStatus.CANCELLED],
            total_goals=len(goals),
            active_sprint=sprint_summary,
        )
