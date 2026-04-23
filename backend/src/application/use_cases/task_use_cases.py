from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.domain.entities import Task
from src.domain.events import (
    IEventBus,
    TaskCreatedEvent,
    TaskDeletedEvent,
    TaskStatusChangedEvent,
    TaskUpdatedEvent,
)
from src.domain.factory import ITaskFactory
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus


@dataclass
class CreateTaskInput:
    task_type: str  # "daily" | "sprint" | "goal" | "milestone"
    title: str
    priority: Priority = Priority.MEDIUM
    estimation: Estimation | None = None
    tags: frozenset[Tag] = field(default_factory=frozenset)
    # DailyTask
    scheduled_date: date | None = None
    # SprintTask
    sprint_id: uuid.UUID | None = None
    # LongTermGoal
    date_range: DateRange | None = None
    # Milestone
    due_date: date | None = None
    goal_id: uuid.UUID | None = None


class CreateTaskUseCase:
    def __init__(
        self,
        repository: ITaskRepository,
        factory: ITaskFactory,
        event_bus: IEventBus,
    ) -> None:
        self._repo = repository
        self._factory = factory
        self._event_bus = event_bus

    async def execute(self, input: CreateTaskInput) -> Task:
        task_type = input.task_type
        base = dict(priority=input.priority, tags=input.tags)
        if task_type == "daily":
            task = self._factory.create_daily(
                input.title,
                scheduled_date=input.scheduled_date,
                estimation=input.estimation,
                **base,
            )
        elif task_type == "sprint":
            task = self._factory.create_sprint(
                input.title,
                sprint_id=input.sprint_id,
                estimation=input.estimation,
                **base,
            )
        elif task_type == "goal":
            task = self._factory.create_goal(
                input.title, date_range=input.date_range, **base
            )
        elif task_type == "milestone":
            task = self._factory.create_milestone(
                input.title, due_date=input.due_date, goal_id=input.goal_id, **base
            )
        else:
            raise ValueError(f"Unknown task_type: {task_type!r}")

        await self._repo.save(task)
        self._event_bus.publish(TaskCreatedEvent(task.id, task.task_type))
        return task


@dataclass
class UpdateTaskInput:
    task_id: uuid.UUID
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    estimation: Estimation | None = None


class UpdateTaskUseCase:
    def __init__(self, repository: ITaskRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, input: UpdateTaskInput) -> Task:
        task = await self._repo.get_by_id(input.task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(input.task_id))

        changed: list[str] = []
        if input.title is not None:
            task.update_title(input.title)
            changed.append("title")
        if input.description is not None:
            task.update_description(input.description)
            changed.append("description")
        if input.priority is not None:
            task.update_priority(input.priority)
            changed.append("priority")
        if input.estimation is not None:
            task.set_estimation(input.estimation)
            changed.append("estimation")

        await self._repo.save(task)
        if changed:
            self._event_bus.publish(TaskUpdatedEvent(task.id, changed))
        return task


class TransitionTaskUseCase:
    def __init__(self, repository: ITaskRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, task_id: uuid.UUID, new_status: TaskStatus) -> Task:
        task = await self._repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))

        old_status = task.status
        try:
            task.transition_to(new_status)
        except ValueError as exc:
            raise InvalidOperationError(str(exc)) from exc

        await self._repo.save(task)
        self._event_bus.publish(
            TaskStatusChangedEvent(task.id, old_status.value, new_status.value)
        )
        return task


class DeleteTaskUseCase:
    def __init__(self, repository: ITaskRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, task_id: uuid.UUID) -> None:
        task = await self._repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))
        await self._repo.delete(task_id)
        self._event_bus.publish(TaskDeletedEvent(task_id))
