from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


class IDomainEvent(ABC):
    def __init__(self) -> None:
        self.event_id: uuid.UUID = uuid.uuid4()
        self.occurred_at: datetime = _now()

    @property
    @abstractmethod
    def event_type(self) -> str: ...


class TaskCreatedEvent(IDomainEvent):
    def __init__(self, task_id: uuid.UUID, task_type: str) -> None:
        super().__init__()
        self.task_id = task_id
        self.task_type = task_type

    @property
    def event_type(self) -> str:
        return "task.created"


class TaskUpdatedEvent(IDomainEvent):
    def __init__(self, task_id: uuid.UUID, changed_fields: list[str]) -> None:
        super().__init__()
        self.task_id = task_id
        self.changed_fields = changed_fields

    @property
    def event_type(self) -> str:
        return "task.updated"


class TaskStatusChangedEvent(IDomainEvent):
    def __init__(
        self,
        task_id: uuid.UUID,
        old_status: str,
        new_status: str,
    ) -> None:
        super().__init__()
        self.task_id = task_id
        self.old_status = old_status
        self.new_status = new_status

    @property
    def event_type(self) -> str:
        return "task.status_changed"


class SprintStartedEvent(IDomainEvent):
    def __init__(self, sprint_id: uuid.UUID, start_date: date) -> None:
        super().__init__()
        self.sprint_id = sprint_id
        self.start_date = start_date

    @property
    def event_type(self) -> str:
        return "sprint.started"


class SprintCompletedEvent(IDomainEvent):
    def __init__(self, sprint_id: uuid.UUID, completed_at: datetime) -> None:
        super().__init__()
        self.sprint_id = sprint_id
        self.completed_at = completed_at

    @property
    def event_type(self) -> str:
        return "sprint.completed"


class GoalProgressEvent(IDomainEvent):
    def __init__(self, goal_id: uuid.UUID, progress_percent: float) -> None:
        if not (0.0 <= progress_percent <= 100.0):
            raise ValueError("progress_percent must be between 0.0 and 100.0")
        super().__init__()
        self.goal_id = goal_id
        self.progress_percent = progress_percent

    @property
    def event_type(self) -> str:
        return "goal.progress"


class IEventHandler(ABC):
    @abstractmethod
    def handle(self, event: IDomainEvent) -> None: ...


class IEventBus(ABC):
    @abstractmethod
    def publish(self, event: IDomainEvent) -> None: ...

    @abstractmethod
    def subscribe(
        self,
        event_type: type[IDomainEvent],
        handler: IEventHandler,
    ) -> None: ...


class InMemoryEventBus(IEventBus):
    def __init__(self) -> None:
        self._handlers: dict[type[IDomainEvent], list[IEventHandler]] = {}

    def subscribe(
        self,
        event_type: type[IDomainEvent],
        handler: IEventHandler,
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: IDomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler.handle(event)
