from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.api.schemas.common import PriorityLiteral, StatusLiteral
from src.application.use_cases.task_use_cases import UNSET, CreateTaskInput, UpdateTaskInput
from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask, Task
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus


class TaskCreateRequest(BaseModel):
    task_type: Literal["daily", "sprint", "goal", "milestone"]
    title: str = Field(min_length=1, max_length=200)
    priority: PriorityLiteral = "medium"
    estimation: int | None = Field(None, ge=1, le=100)
    tags: list[str] = []
    # DailyTask
    scheduled_date: date | None = None
    # SprintTask
    sprint_id: uuid.UUID | None = None
    # LongTermGoal
    date_range_start: date | None = None
    date_range_end: date | None = None
    # Milestone
    due_date: date | None = None
    goal_id: uuid.UUID | None = None

    def to_use_case_input(self) -> CreateTaskInput:
        date_range = (
            DateRange(self.date_range_start, self.date_range_end)
            if self.date_range_start and self.date_range_end
            else None
        )
        return CreateTaskInput(
            task_type=self.task_type,
            title=self.title,
            priority=Priority(self.priority),
            estimation=Estimation(self.estimation) if self.estimation else None,
            tags=frozenset(Tag(t) for t in self.tags),
            scheduled_date=self.scheduled_date,
            sprint_id=self.sprint_id,
            date_range=date_range,
            due_date=self.due_date,
            goal_id=self.goal_id,
        )


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    priority: PriorityLiteral | None = None
    estimation: int | None = Field(None, ge=1, le=100)
    tags: list[str] | None = None
    due_date: date | None = None

    def to_use_case_input(self, task_id: uuid.UUID) -> UpdateTaskInput:
        return UpdateTaskInput(
            task_id=task_id,
            title=self.title,
            description=self.description,
            priority=Priority(self.priority) if self.priority else None,
            estimation=Estimation(self.estimation) if self.estimation else None,
            tags=frozenset(Tag(t) for t in self.tags) if self.tags is not None else None,
            due_date=self.due_date if "due_date" in self.model_fields_set else UNSET,
        )


class TaskTransitionRequest(BaseModel):
    status: StatusLiteral

    def to_task_status(self) -> TaskStatus:
        return TaskStatus(self.status)


class TaskResponse(BaseModel):
    id: uuid.UUID
    task_type: str
    title: str
    description: str
    status: str
    priority: str
    estimation: int | None
    tags: list[str]
    scheduled_date: date | None
    sprint_id: uuid.UUID | None
    date_range_start: date | None
    date_range_end: date | None
    due_date: date | None
    goal_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, task: Task) -> TaskResponse:
        return cls(
            id=task.id,
            task_type=task.task_type,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            estimation=task.estimation.story_points if task.estimation else None,
            tags=sorted(t.name for t in task.tags),
            scheduled_date=task.scheduled_date if isinstance(task, DailyTask) else None,
            sprint_id=task.sprint_id if isinstance(task, SprintTask) else None,
            date_range_start=(
                task.date_range.start
                if isinstance(task, LongTermGoal) and task.date_range
                else None
            ),
            date_range_end=(
                task.date_range.end
                if isinstance(task, LongTermGoal) and task.date_range
                else None
            ),
            due_date=task.due_date if isinstance(task, Milestone) else None,
            goal_id=task.goal_id if isinstance(task, Milestone) else None,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
