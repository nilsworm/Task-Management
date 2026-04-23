from __future__ import annotations

import uuid
from datetime import date

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


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

class MetricsResponse(BaseModel):
    task_counts: TaskStatusCounts
    completion_rate: float  # done / (total - cancelled) * 100, 0.0 if no tasks


# ---------------------------------------------------------------------------
# Burndown
# ---------------------------------------------------------------------------

class BurndownPoint(BaseModel):
    date: date
    remaining_points: int


class BurndownResponse(BaseModel):
    sprint_id: uuid.UUID
    sprint_name: str
    start_date: date
    end_date: date
    total_points: int
    ideal_line: list[BurndownPoint]   # linear from total → 0 over sprint duration
    actual_remaining: int             # current remaining story points


# ---------------------------------------------------------------------------
# Velocity
# ---------------------------------------------------------------------------

class SprintVelocity(BaseModel):
    sprint_id: uuid.UUID
    sprint_name: str
    completed_points: int


class VelocityResponse(BaseModel):
    sprints: list[SprintVelocity]
    average_velocity: float


# ---------------------------------------------------------------------------
# Goal Progress
# ---------------------------------------------------------------------------

class GoalProgressItem(BaseModel):
    goal_id: uuid.UUID
    goal_title: str
    progress_percent: float
    key_results_count: int


class GoalProgressResponse(BaseModel):
    goals: list[GoalProgressItem]
