from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import final

from src.domain.states import StateFactory
from src.domain.value_objects import (
    DateRange,
    Estimation,
    Priority,
    Tag,
    TaskStatus,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class KeyResult:
    id: uuid.UUID
    goal_id: uuid.UUID
    title: str
    description: str
    target_value: float
    current_value: float
    unit: str
    created_at: datetime
    updated_at: datetime

    @property
    def progress_percent(self) -> float:
        return min(self.current_value / self.target_value * 100.0, 100.0)


class Task(ABC):
    def __init__(
        self,
        title: str,
        *,
        id: uuid.UUID | None = None,
        description: str = "",
        status: TaskStatus = TaskStatus.BACKLOG,
        priority: Priority = Priority.MEDIUM,
        estimation: Estimation | None = None,
        tags: frozenset[Tag] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self._validate_title(title)
        self.id: uuid.UUID = id or uuid.uuid4()
        self.title: str = title
        self.description: str = description
        self.status: TaskStatus = status
        self.priority: Priority = priority
        self.estimation: Estimation | None = estimation
        self.tags: frozenset[Tag] = tags or frozenset()
        now = _now()
        self.created_at: datetime = created_at or now
        self.updated_at: datetime = updated_at or now

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title.strip():
            raise ValueError("title cannot be empty")
        if len(title) > 200:
            raise ValueError("title cannot exceed 200 characters")

    def transition_to(self, new_status: TaskStatus) -> None:
        state = StateFactory.for_status(self.status)
        if not state.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status.value} to {new_status.value}"
            )
        state.on_enter(self)
        self.status = new_status
        self.updated_at = _now()

    def add_tag(self, tag: Tag) -> None:
        self.tags = self.tags | frozenset({tag})
        self.updated_at = _now()

    def remove_tag(self, tag: Tag) -> None:
        self.tags = self.tags - frozenset({tag})
        self.updated_at = _now()

    def update_title(self, title: str) -> None:
        self._validate_title(title)
        self.title = title
        self.updated_at = _now()

    def update_description(self, description: str) -> None:
        self.description = description
        self.updated_at = _now()

    def update_priority(self, priority: Priority) -> None:
        self.priority = priority
        self.updated_at = _now()

    def set_estimation(self, estimation: Estimation | None) -> None:
        self.estimation = estimation
        self.updated_at = _now()

    @property
    @abstractmethod
    def task_type(self) -> str: ...


@final
class DailyTask(Task):
    def __init__(
        self,
        title: str,
        *,
        scheduled_date: date | None = None,
        **kwargs,
    ) -> None:
        super().__init__(title, **kwargs)
        self.scheduled_date: date | None = scheduled_date

    @property
    def task_type(self) -> str:
        return "daily"


@final
class SprintTask(Task):
    def __init__(
        self,
        title: str,
        *,
        sprint_id: uuid.UUID | None = None,
        **kwargs,
    ) -> None:
        super().__init__(title, **kwargs)
        self.sprint_id: uuid.UUID | None = sprint_id

    @property
    def story_points(self) -> int | None:
        return self.estimation.story_points if self.estimation else None

    @property
    def task_type(self) -> str:
        return "sprint"


@final
class LongTermGoal(Task):
    def __init__(
        self,
        title: str,
        *,
        date_range: DateRange | None = None,
        **kwargs,
    ) -> None:
        super().__init__(title, **kwargs)
        self.date_range: DateRange | None = date_range

    @property
    def task_type(self) -> str:
        return "goal"


@final
class Milestone(Task):
    def __init__(
        self,
        title: str,
        *,
        due_date: date | None = None,
        goal_id: uuid.UUID | None = None,
        **kwargs,
    ) -> None:
        super().__init__(title, **kwargs)
        self.due_date: date | None = due_date
        self.goal_id: uuid.UUID | None = goal_id

    @property
    def task_type(self) -> str:
        return "milestone"
