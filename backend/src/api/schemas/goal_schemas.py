from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from src.api.schemas.common import PriorityLiteral
from src.application.use_cases.goal_use_cases import (
    CreateKeyResultInput,
    UpdateGoalInput,
    UpdateKeyResultInput,
)
from src.domain.entities import KeyResult, LongTermGoal
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

    def to_use_case_input(self, goal_id: uuid.UUID) -> UpdateGoalInput:
        date_range = (
            DateRange(self.date_range_start, self.date_range_end)
            if self.date_range_start and self.date_range_end
            else None
        )
        return UpdateGoalInput(
            goal_id=goal_id,
            title=self.title,
            description=self.description,
            priority=Priority(self.priority) if self.priority else None,
            tags=frozenset(Tag(t) for t in self.tags) if self.tags is not None else None,
            date_range=date_range,
        )


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

    def to_use_case_input(self, goal_id: uuid.UUID) -> CreateKeyResultInput:
        return CreateKeyResultInput(
            goal_id=goal_id,
            title=self.title,
            description=self.description,
            target_value=self.target_value,
            current_value=self.current_value,
            unit=self.unit,
        )


class KeyResultUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    current_value: float | None = Field(None, ge=0)
    target_value: float | None = Field(None, gt=0)
    unit: str | None = None

    def to_use_case_input(self, key_result_id: uuid.UUID) -> UpdateKeyResultInput:
        return UpdateKeyResultInput(
            key_result_id=key_result_id,
            title=self.title,
            description=self.description,
            current_value=self.current_value,
            target_value=self.target_value,
            unit=self.unit,
        )


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

    @classmethod
    def from_domain(cls, kr: KeyResult) -> KeyResultResponse:
        return cls(
            id=kr.id,
            goal_id=kr.goal_id,
            title=kr.title,
            description=kr.description,
            target_value=kr.target_value,
            current_value=kr.current_value,
            unit=kr.unit,
            progress_percent=kr.progress_percent,
            created_at=kr.created_at,
            updated_at=kr.updated_at,
        )
