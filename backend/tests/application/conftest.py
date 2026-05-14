from __future__ import annotations

import uuid

import pytest

from src.domain.entities import KeyResult, LongTermGoal, SprintTask, Task
from src.domain.events import IDomainEvent, IEventHandler, InMemoryEventBus
from src.domain.factory import TaskFactory
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import TaskStatus


class InMemoryTaskRepository(ITaskRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Task] = {}

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        return self._store.get(task_id)

    async def save(self, task: Task) -> None:
        self._store[task.id] = task

    async def delete(self, task_id: uuid.UUID) -> None:
        self._store.pop(task_id, None)

    async def list_all(self) -> list[Task]:
        return list(self._store.values())

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        return [t for t in self._store.values() if t.status == status]

    async def list_by_sprint(
        self,
        sprint_id: uuid.UUID,
        status_filter: TaskStatus | None = None,
    ) -> list[SprintTask]:
        tasks = [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id == sprint_id
        ]
        if status_filter is not None:
            tasks = [t for t in tasks if t.status == status_filter]
        return tasks

    async def list_by_sprint_ids(
        self, sprint_ids: list[uuid.UUID]
    ) -> list[SprintTask]:
        return [
            t for t in self._store.values()
            if isinstance(t, SprintTask) and t.sprint_id in sprint_ids
        ]

    async def list_by_search(self, query: str) -> list[Task]:
        q = query.lower()
        return [t for t in self._store.values() if q in t.title.lower()]


class InMemorySprintRepository(ISprintRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, Sprint] = {}

    async def get_by_id(self, sprint_id: uuid.UUID) -> Sprint | None:
        return self._store.get(sprint_id)

    async def save(self, sprint: Sprint) -> None:
        self._store[sprint.id] = sprint

    async def delete(self, sprint_id: uuid.UUID) -> None:
        self._store.pop(sprint_id, None)

    async def list_all(self) -> list[Sprint]:
        return list(self._store.values())

    async def get_active(self) -> Sprint | None:
        for sprint in self._store.values():
            if sprint.status is SprintStatus.ACTIVE:
                return sprint
        return None


class InMemoryGoalRepository(IGoalRepository):
    def __init__(self) -> None:
        self._store: dict[uuid.UUID, LongTermGoal] = {}
        self._key_results: dict[uuid.UUID, KeyResult] = {}

    async def get_by_id(self, goal_id: uuid.UUID) -> LongTermGoal | None:
        return self._store.get(goal_id)

    async def save(self, goal: LongTermGoal) -> None:
        self._store[goal.id] = goal

    async def delete(self, goal_id: uuid.UUID) -> None:
        self._store.pop(goal_id, None)

    async def list_all(self) -> list[LongTermGoal]:
        return list(self._store.values())

    async def list_key_results(self, goal_id: uuid.UUID) -> list[KeyResult]:
        return [kr for kr in self._key_results.values() if kr.goal_id == goal_id]

    async def list_all_key_results(self) -> list[KeyResult]:
        return list(self._key_results.values())

    async def get_key_result(self, key_result_id: uuid.UUID) -> KeyResult | None:
        return self._key_results.get(key_result_id)

    async def save_key_result(self, key_result: KeyResult) -> None:
        self._key_results[key_result.id] = key_result

    async def delete_key_result(self, key_result_id: uuid.UUID) -> None:
        self._key_results.pop(key_result_id, None)


class EventSpy(IEventHandler):
    """Captures all published events for assertion in tests."""

    def __init__(self) -> None:
        self.events: list[IDomainEvent] = []

    def handle(self, event: IDomainEvent) -> None:
        self.events.append(event)


@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def sprint_repo() -> InMemorySprintRepository:
    return InMemorySprintRepository()


@pytest.fixture
def goal_repo() -> InMemoryGoalRepository:
    return InMemoryGoalRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()
