from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from src.domain.value_objects import DateRange


class SprintStatus(enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Sprint:
    def __init__(
        self,
        name: str,
        date_range: DateRange,
        *,
        id: uuid.UUID | None = None,
        status: SprintStatus = SprintStatus.PLANNED,
        task_ids: list[uuid.UUID] | None = None,
        goal: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        if not name.strip():
            raise ValueError("Sprint name cannot be empty")
        self.id: uuid.UUID = id or uuid.uuid4()
        self.name: str = name
        self.date_range: DateRange = date_range
        self.status: SprintStatus = status
        self.task_ids: list[uuid.UUID] = task_ids or []
        self.goal: str | None = goal
        self.created_at: datetime = created_at or _now()

    def add_task(self, task_id: uuid.UUID) -> None:
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)

    def remove_task(self, task_id: uuid.UUID) -> None:
        self.task_ids = [t for t in self.task_ids if t != task_id]

    def start(self) -> None:
        if self.status is not SprintStatus.PLANNED:
            raise ValueError(f"Cannot start a sprint in status '{self.status.value}'")
        self.status = SprintStatus.ACTIVE

    def complete(self) -> None:
        if self.status is not SprintStatus.ACTIVE:
            raise ValueError(f"Cannot complete a sprint in status '{self.status.value}'")
        self.status = SprintStatus.COMPLETED

    def cancel(self) -> None:
        if self.status in (SprintStatus.COMPLETED, SprintStatus.CANCELLED):
            raise ValueError(f"Cannot cancel a sprint in status '{self.status.value}'")
        self.status = SprintStatus.CANCELLED
