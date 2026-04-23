from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import date


class Priority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(enum.Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    BLOCKED = "blocked"
    DONE = "done"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Estimation:
    story_points: int

    def __post_init__(self) -> None:
        if self.story_points < 1:
            raise ValueError("story_points must be >= 1")
        if self.story_points > 100:
            raise ValueError("story_points must be <= 100")


@dataclass(frozen=True)
class DateRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise ValueError("end must not be before start")

    @property
    def duration_days(self) -> int:
        return (self.end - self.start).days + 1


@dataclass(frozen=True)
class Tag:
    name: str

    def __post_init__(self) -> None:
        normalized = self.name.strip().lower()
        if not normalized:
            raise ValueError("Tag name cannot be empty")
        if len(normalized) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
        object.__setattr__(self, "name", normalized)


@dataclass(frozen=True)
class BurndownPoint:
    date: date
    remaining_points: int

    def __post_init__(self) -> None:
        if self.remaining_points < 0:
            raise ValueError("remaining_points cannot be negative")
