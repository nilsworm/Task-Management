"""Verify that use cases raise the correct application-layer exception types."""
from __future__ import annotations

import uuid
from datetime import date

import pytest

from src.application.exceptions import EntityNotFoundError, InvalidOperationError
from src.application.use_cases.sprint_use_cases import (
    CompleteSprintUseCase,
    StartSprintUseCase,
)
from src.application.use_cases.task_use_cases import (
    CreateTaskInput,
    DeleteTaskUseCase,
    TransitionTaskUseCase,
    UpdateTaskInput,
    UpdateTaskUseCase,
)
from src.domain.events import InMemoryEventBus
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint
from src.domain.value_objects import DateRange, TaskStatus

from tests.application.conftest import InMemorySprintRepository, InMemoryTaskRepository


@pytest.fixture
def task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def sprint_repo() -> InMemorySprintRepository:
    return InMemorySprintRepository()


@pytest.fixture
def event_bus() -> InMemoryEventBus:
    return InMemoryEventBus()


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()


def _task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()



def _task_repo() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()

def _sprint() -> Sprint:
    return Sprint("S1", DateRange(date(2026, 5, 1), date(2026, 5, 14)))


# ---------------------------------------------------------------------------
# Task use cases — EntityNotFoundError
# ---------------------------------------------------------------------------

async def test_update_missing_task_raises_not_found(
    task_repo: InMemoryTaskRepository, event_bus: InMemoryEventBus
) -> None:
    with pytest.raises(EntityNotFoundError):
        await UpdateTaskUseCase(task_repo, event_bus).execute(
            UpdateTaskInput(task_id=uuid.uuid4(), title="x")
        )


async def test_transition_missing_task_raises_not_found(
    task_repo: InMemoryTaskRepository, event_bus: InMemoryEventBus
) -> None:
    with pytest.raises(EntityNotFoundError):
        await TransitionTaskUseCase(task_repo, event_bus).execute(
            uuid.uuid4(), TaskStatus.TODO
        )


async def test_delete_missing_task_raises_not_found(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
) -> None:
    with pytest.raises(EntityNotFoundError):
        await DeleteTaskUseCase(task_repo, event_bus).execute(uuid.uuid4())


# ---------------------------------------------------------------------------
# Task use cases — InvalidOperationError
# ---------------------------------------------------------------------------

async def test_invalid_transition_raises_invalid_operation(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)
    # BACKLOG → DONE is not allowed
    with pytest.raises(InvalidOperationError):
        await TransitionTaskUseCase(task_repo, event_bus).execute(
            task.id, TaskStatus.DONE
        )


# ---------------------------------------------------------------------------
# Sprint use cases — EntityNotFoundError
# ---------------------------------------------------------------------------

async def test_start_missing_sprint_raises_not_found(
    sprint_repo: InMemorySprintRepository, event_bus: InMemoryEventBus
) -> None:
    with pytest.raises(EntityNotFoundError):
        await StartSprintUseCase(sprint_repo, event_bus).execute(uuid.uuid4())


async def test_complete_missing_sprint_raises_not_found(
    sprint_repo: InMemorySprintRepository, event_bus: InMemoryEventBus
) -> None:
    with pytest.raises(EntityNotFoundError):
        await CompleteSprintUseCase(sprint_repo, _task_repo(), event_bus).execute(uuid.uuid4())


# ---------------------------------------------------------------------------
# Sprint use cases — InvalidOperationError
# ---------------------------------------------------------------------------

async def test_start_active_sprint_raises_invalid_operation(
    sprint_repo: InMemorySprintRepository, event_bus: InMemoryEventBus
) -> None:
    sprint = _sprint()
    sprint.start()
    await sprint_repo.save(sprint)
    with pytest.raises(InvalidOperationError):
        await StartSprintUseCase(sprint_repo, event_bus).execute(sprint.id)


async def test_complete_planned_sprint_raises_invalid_operation(
    sprint_repo: InMemorySprintRepository, event_bus: InMemoryEventBus
) -> None:
    sprint = _sprint()
    await sprint_repo.save(sprint)
    with pytest.raises(InvalidOperationError):
        await CompleteSprintUseCase(sprint_repo, _task_repo(), event_bus).execute(sprint.id)
