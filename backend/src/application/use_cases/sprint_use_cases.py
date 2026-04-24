from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.domain.events import IEventBus, SprintCompletedEvent, SprintDeletedEvent, SprintStartedEvent
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange


class CreateSprintUseCase:
    def __init__(self, repository: ISprintRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, name: str, date_range: DateRange, goal: str | None = None) -> Sprint:
        sprint = Sprint(name, date_range, goal=goal)
        await self._repo.save(sprint)
        self._event_bus.publish(SprintStartedEvent(sprint.id, date_range.start))
        return sprint


class StartSprintUseCase:
    def __init__(self, repository: ISprintRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, sprint_id: uuid.UUID) -> Sprint:
        sprint = await self._repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        try:
            sprint.start()
        except ValueError as exc:
            raise InvalidOperationError(str(exc)) from exc
        await self._repo.save(sprint)
        self._event_bus.publish(SprintStartedEvent(sprint.id, sprint.date_range.start))
        return sprint


class CompleteSprintUseCase:
    def __init__(self, repository: ISprintRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, sprint_id: uuid.UUID) -> Sprint:
        sprint = await self._repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        try:
            sprint.complete()
        except ValueError as exc:
            raise InvalidOperationError(str(exc)) from exc
        await self._repo.save(sprint)
        self._event_bus.publish(
            SprintCompletedEvent(sprint.id, datetime.now(timezone.utc))
        )
        return sprint


class UpdateSprintUseCase:
    def __init__(self, repository: ISprintRepository) -> None:
        self._repo = repository

    async def execute(
        self,
        sprint_id: uuid.UUID,
        name: str | None = None,
        goal: str | None = None,
    ) -> Sprint:
        sprint = await self._repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        if name is not None:
            sprint.name = name
        if goal is not None:
            sprint.goal = goal
        await self._repo.save(sprint)
        return sprint


class DeleteSprintUseCase:
    def __init__(self, repository: ISprintRepository, event_bus: IEventBus) -> None:
        self._repo = repository
        self._event_bus = event_bus

    async def execute(self, sprint_id: uuid.UUID) -> None:
        sprint = await self._repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        if sprint.status.value == "active":
            raise InvalidOperationError(
                f"Cannot delete active sprint '{sprint.name}'. Complete or cancel it first."
            )
        await self._repo.delete(sprint_id)
        self._event_bus.publish(SprintDeletedEvent(sprint_id))


class AddTaskToSprintUseCase:
    def __init__(
        self,
        sprint_repo: ISprintRepository,
        task_repo: ITaskRepository,
    ) -> None:
        self._sprint_repo = sprint_repo
        self._task_repo = task_repo

    async def execute(self, sprint_id: uuid.UUID, task_id: uuid.UUID) -> Sprint:
        sprint = await self._sprint_repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))
        sprint.add_task(task_id)
        await self._sprint_repo.save(sprint)
        return sprint


class RemoveTaskFromSprintUseCase:
    def __init__(
        self,
        sprint_repo: ISprintRepository,
        task_repo: ITaskRepository,
    ) -> None:
        self._sprint_repo = sprint_repo
        self._task_repo = task_repo

    async def execute(self, sprint_id: uuid.UUID, task_id: uuid.UUID) -> None:
        sprint = await self._sprint_repo.get_by_id(sprint_id)
        if sprint is None:
            raise EntityNotFoundError("Sprint", str(sprint_id))
        task = await self._task_repo.get_by_id(task_id)
        if task is None:
            raise EntityNotFoundError("Task", str(task_id))
        sprint.remove_task(task_id)
        await self._sprint_repo.save(sprint)
