from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange


class SprintCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    start_date: date
    end_date: date

    def to_date_range(self) -> DateRange:
        return DateRange(self.start_date, self.end_date)


class SprintUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)


class SprintResponse(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    start_date: date
    end_date: date
    task_ids: list[uuid.UUID]
    created_at: datetime

    @classmethod
    def from_domain(cls, sprint: Sprint) -> SprintResponse:
        return cls(
            id=sprint.id,
            name=sprint.name,
            status=sprint.status.value,
            start_date=sprint.date_range.start,
            end_date=sprint.date_range.end,
            task_ids=sprint.task_ids,
            created_at=sprint.created_at,
        )
