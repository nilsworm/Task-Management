from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from src.api.schemas.common import PriorityLiteral
from src.domain.entities import LongTermGoal
from src.domain.value_objects import DateRange, Priority, Tag, TaskStatus


class GoalCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    priority: PriorityLiteral = "medium"
    tags: list[str] = []
    date_range_start: date | None = None
    date_range_end: date | None = None

    def to_domain(self) -> LongTermGoal:
        date_range = (
            DateRange(self.date_range_start, self.date_range_end)
            if self.date_range_start and self.date_range_end
            else None
        )
        return LongTermGoal(
            self.title,
            description=self.description,
            priority=Priority(self.priority),
            tags=frozenset(Tag(t) for t in self.tags),
            date_range=date_range,
            status=TaskStatus.BACKLOG,
        )


class GoalUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    priority: PriorityLiteral | None = None
    tags: list[str] | None = None
    date_range_start: date | None = None
    date_range_end: date | None = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: str
    priority: str
    tags: list[str]
    date_range_start: date | None
    date_range_end: date | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, goal: LongTermGoal) -> GoalResponse:
        return cls(
            id=goal.id,
            title=goal.title,
            description=goal.description,
            status=goal.status.value,
            priority=goal.priority.value,
            tags=sorted(t.name for t in goal.tags),
            date_range_start=goal.date_range.start if goal.date_range else None,
            date_range_end=goal.date_range.end if goal.date_range else None,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )


class KeyResultCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    target_value: float = Field(gt=0)
    current_value: float = Field(ge=0, default=0.0)
    unit: str = ""


class KeyResultUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    current_value: float | None = Field(None, ge=0)
    target_value: float | None = Field(None, gt=0)
    unit: str | None = None


class KeyResultResponse(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    title: str
    description: str
    target_value: float
    current_value: float
    unit: str
    progress_percent: float
    created_at: datetime
    updated_at: datetime
