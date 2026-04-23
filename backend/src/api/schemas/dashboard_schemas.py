from __future__ import annotations

from pydantic import BaseModel


class TaskStatusCounts(BaseModel):
    backlog: int
    todo: int
    in_progress: int
    review: int
    blocked: int
    done: int
    cancelled: int


class SprintSummary(BaseModel):
    id: str
    name: str
    status: str
    total_tasks: int
    done_tasks: int
    completion_percent: float


class DashboardResponse(BaseModel):
    total_tasks: int
    task_counts: TaskStatusCounts
    total_goals: int
    active_sprint: SprintSummary | None
