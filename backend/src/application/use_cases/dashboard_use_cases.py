from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta

from src.application.exceptions import EntityNotFoundError
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.sprint import SprintStatus
from src.domain.value_objects import TaskStatus


# ---------------------------------------------------------------------------
# GetDashboardUseCase (summary)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GetDashboardMetricsUseCase
# ---------------------------------------------------------------------------

@dataclass
class MetricsData:
    backlog: int
    todo: int
    in_progress: int
    review: int
    blocked: int
    done: int
    cancelled: int
    completion_rate: float  # done / (total - cancelled) * 100


class GetDashboardMetricsUseCase:
    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(self) -> MetricsData:
        tasks = await self._task_repo.list_all()
        counts = {s: 0 for s in TaskStatus}
        for t in tasks:
            counts[t.status] += 1

        eligible = len(tasks) - counts[TaskStatus.CANCELLED]
        completion_rate = round(
            counts[TaskStatus.DONE] / eligible * 100.0 if eligible else 0.0, 1
        )
        return MetricsData(
            backlog=counts[TaskStatus.BACKLOG],
            todo=counts[TaskStatus.TODO],
            in_progress=counts[TaskStatus.IN_PROGRESS],
            review=counts[TaskStatus.REVIEW],
            blocked=counts[TaskStatus.BLOCKED],
            done=counts[TaskStatus.DONE],
            cancelled=counts[TaskStatus.CANCELLED],
            completion_rate=completion_rate,
        )


# ---------------------------------------------------------------------------
# GetSprintBurndownUseCase
# ---------------------------------------------------------------------------

@dataclass
class BurndownPointData:
    date: date
    remaining_points: int


@dataclass
class BurndownData:
    sprint_id: uuid.UUID
    sprint_name: str
    start_date: date
    end_date: date
    total_points: int
    ideal_line: list[BurndownPointData]
    actual_remaining: int


class GetSprintBurndownUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        sprint_repo: ISprintRepository,
    ) -> None:
        self._task_repo = task_repo
        self._sprint_repo = sprint_repo

    async def execute(self, sprint_id: uuid.UUID | None = None) -> BurndownData:
        if sprint_id is not None:
            sprint = await self._sprint_repo.get_by_id(sprint_id)
            if sprint is None:
                raise EntityNotFoundError("Sprint", str(sprint_id))
        else:
            sprint = await self._sprint_repo.get_active()
            if sprint is None:
                raise EntityNotFoundError("Sprint", "active")

        sprint_tasks = await self._task_repo.list_by_sprint(sprint.id)
        total_points = sum(
            t.estimation.story_points for t in sprint_tasks if t.estimation
        )
        done_points = sum(
            t.estimation.story_points
            for t in sprint_tasks
            if t.status == TaskStatus.DONE and t.estimation
        )
        actual_remaining = total_points - done_points

        # Build ideal burndown line: linear from total → 0
        start = sprint.date_range.start
        end = sprint.date_range.end
        days = (end - start).days + 1
        ideal_line = [
            BurndownPointData(
                date=start + timedelta(days=i),
                remaining_points=round(total_points * (1 - i / (days - 1))) if days > 1 else 0,
            )
            for i in range(days)
        ]

        return BurndownData(
            sprint_id=sprint.id,
            sprint_name=sprint.name,
            start_date=start,
            end_date=end,
            total_points=total_points,
            ideal_line=ideal_line,
            actual_remaining=actual_remaining,
        )


# ---------------------------------------------------------------------------
# GetVelocityUseCase
# ---------------------------------------------------------------------------

@dataclass
class SprintVelocityData:
    sprint_id: uuid.UUID
    sprint_name: str
    completed_points: int


@dataclass
class VelocityData:
    sprints: list[SprintVelocityData]
    average_velocity: float


class GetVelocityUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        sprint_repo: ISprintRepository,
    ) -> None:
        self._task_repo = task_repo
        self._sprint_repo = sprint_repo

    async def execute(self, last_n: int = 5) -> VelocityData:
        all_sprints = await self._sprint_repo.list_all()
        completed = [s for s in all_sprints if s.status is SprintStatus.COMPLETED]
        recent = sorted(completed, key=lambda s: s.created_at, reverse=True)[:last_n]

        all_tasks = await self._task_repo.list_by_sprint_ids([s.id for s in recent])
        tasks_by_sprint: dict[uuid.UUID, list] = {}
        for t in all_tasks:
            if t.sprint_id is not None:
                tasks_by_sprint.setdefault(t.sprint_id, []).append(t)

        results: list[SprintVelocityData] = []
        for sprint in recent:
            sprint_tasks = tasks_by_sprint.get(sprint.id, [])
            points = sum(
                t.estimation.story_points
                for t in sprint_tasks
                if t.status == TaskStatus.DONE and t.estimation
            )
            results.append(SprintVelocityData(
                sprint_id=sprint.id,
                sprint_name=sprint.name,
                completed_points=points,
            ))

        avg = round(
            sum(r.completed_points for r in results) / len(results) if results else 0.0,
            1,
        )
        return VelocityData(sprints=results, average_velocity=avg)


# ---------------------------------------------------------------------------
# GetGoalProgressUseCase
# ---------------------------------------------------------------------------

@dataclass
class GoalProgressItemData:
    goal_id: uuid.UUID
    goal_title: str
    progress_percent: float
    key_results_count: int


@dataclass
class GoalProgressData:
    goals: list[GoalProgressItemData]


class GetGoalProgressUseCase:
    def __init__(self, goal_repo: IGoalRepository) -> None:
        self._goal_repo = goal_repo

    async def execute(self) -> GoalProgressData:
        goals = await self._goal_repo.list_all()
        all_krs = await self._goal_repo.list_all_key_results()
        krs_by_goal: dict[uuid.UUID, list] = {}
        for kr in all_krs:
            krs_by_goal.setdefault(kr.goal_id, []).append(kr)

        items: list[GoalProgressItemData] = []
        for goal in goals:
            krs = krs_by_goal.get(goal.id, [])
            avg_progress = round(
                sum(kr.progress_percent for kr in krs) / len(krs), 1
            ) if krs else 0.0
            items.append(GoalProgressItemData(
                goal_id=goal.id,
                goal_title=goal.title,
                progress_percent=avg_progress,
                key_results_count=len(krs),
            ))
        return GoalProgressData(goals=items)
