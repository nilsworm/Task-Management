from __future__ import annotations

import uuid
from datetime import date

import pytest

from src.application.exceptions import InvalidOperationError
from src.application.use_cases.sprint_use_cases import (
    AddTaskToSprintUseCase,
    CompleteSprintUseCase,
    CreateSprintUseCase,
    DeleteSprintUseCase,
    StartSprintUseCase,
    UpdateSprintUseCase,
)
from src.domain.events import (
    InMemoryEventBus,
    SprintCompletedEvent,
    SprintDeletedEvent,
    SprintStartedEvent,
)
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange

from .conftest import EventSpy, InMemorySprintRepository, InMemoryTaskRepository


def _date_range() -> DateRange:
    return DateRange(date(2026, 5, 1), date(2026, 5, 14))


# ---------------------------------------------------------------------------
# CreateSprintUseCase
# ---------------------------------------------------------------------------

async def test_create_sprint_saves_and_returns(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateSprintUseCase(sprint_repo, event_bus)
    sprint = await use_case.execute("Sprint 1", _date_range())

    assert sprint.name == "Sprint 1"
    assert sprint.status is SprintStatus.PLANNED
    saved = await sprint_repo.get_by_id(sprint.id)
    assert saved is sprint


async def test_create_sprint_publishes_started_event(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    spy = EventSpy()
    event_bus.subscribe(SprintStartedEvent, spy)

    use_case = CreateSprintUseCase(sprint_repo, event_bus)
    sprint = await use_case.execute("Sprint 1", _date_range())

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, SprintStartedEvent)
    assert event.sprint_id == sprint.id
    assert event.start_date == _date_range().start


# ---------------------------------------------------------------------------
# StartSprintUseCase
# ---------------------------------------------------------------------------

async def test_start_sprint_changes_status_to_active(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)

    use_case = StartSprintUseCase(sprint_repo, event_bus)
    result = await use_case.execute(sprint.id)

    assert result.status is SprintStatus.ACTIVE
    assert (await sprint_repo.get_by_id(sprint.id)).status is SprintStatus.ACTIVE  # type: ignore[union-attr]


async def test_start_sprint_publishes_started_event(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)

    spy = EventSpy()
    event_bus.subscribe(SprintStartedEvent, spy)

    use_case = StartSprintUseCase(sprint_repo, event_bus)
    await use_case.execute(sprint.id)

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, SprintStartedEvent)
    assert event.sprint_id == sprint.id


async def test_start_sprint_not_found_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = StartSprintUseCase(sprint_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(uuid.uuid4())


async def test_start_sprint_already_active_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    sprint.start()
    await sprint_repo.save(sprint)

    use_case = StartSprintUseCase(sprint_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(sprint.id)


# ---------------------------------------------------------------------------
# CompleteSprintUseCase
# ---------------------------------------------------------------------------

async def test_complete_sprint_changes_status(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    sprint.start()
    await sprint_repo.save(sprint)

    use_case = CompleteSprintUseCase(sprint_repo, event_bus)
    result = await use_case.execute(sprint.id)

    assert result.status is SprintStatus.COMPLETED
    assert (await sprint_repo.get_by_id(sprint.id)).status is SprintStatus.COMPLETED  # type: ignore[union-attr]


async def test_complete_sprint_publishes_completed_event(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    sprint.start()
    await sprint_repo.save(sprint)

    spy = EventSpy()
    event_bus.subscribe(SprintCompletedEvent, spy)

    use_case = CompleteSprintUseCase(sprint_repo, event_bus)
    await use_case.execute(sprint.id)

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, SprintCompletedEvent)
    assert event.sprint_id == sprint.id


async def test_complete_sprint_not_found_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CompleteSprintUseCase(sprint_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(uuid.uuid4())


async def test_complete_sprint_from_planned_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)

    use_case = CompleteSprintUseCase(sprint_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(sprint.id)


# ---------------------------------------------------------------------------
# AddTaskToSprintUseCase
# ---------------------------------------------------------------------------

async def test_add_task_to_sprint(
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)
    task = factory.create_daily("Daily task")
    await task_repo.save(task)

    use_case = AddTaskToSprintUseCase(sprint_repo, task_repo)
    result = await use_case.execute(sprint.id, task.id)

    assert task.id in result.task_ids
    saved_sprint = await sprint_repo.get_by_id(sprint.id)
    assert saved_sprint is not None
    assert task.id in saved_sprint.task_ids


async def test_add_task_to_sprint_idempotent(
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = AddTaskToSprintUseCase(sprint_repo, task_repo)
    await use_case.execute(sprint.id, task.id)
    await use_case.execute(sprint.id, task.id)

    saved = await sprint_repo.get_by_id(sprint.id)
    assert saved is not None
    assert saved.task_ids.count(task.id) == 1


async def test_add_task_sprint_not_found_raises(
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = AddTaskToSprintUseCase(sprint_repo, task_repo)
    with pytest.raises(ValueError):
        await use_case.execute(uuid.uuid4(), task.id)


# ---------------------------------------------------------------------------
# CreateSprintUseCase — goal field
# ---------------------------------------------------------------------------

async def test_create_sprint_with_goal(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateSprintUseCase(sprint_repo, event_bus)
    sprint = await use_case.execute("Sprint G", _date_range(), goal="Ship the auth flow")

    assert sprint.goal == "Ship the auth flow"
    saved = await sprint_repo.get_by_id(sprint.id)
    assert saved is not None
    assert saved.goal == "Ship the auth flow"


async def test_create_sprint_goal_defaults_to_none(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateSprintUseCase(sprint_repo, event_bus)
    sprint = await use_case.execute("Sprint N", _date_range())

    assert sprint.goal is None


# ---------------------------------------------------------------------------
# UpdateSprintUseCase
# ---------------------------------------------------------------------------

async def test_update_sprint_name(
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Old Name", _date_range())
    await sprint_repo.save(sprint)

    result = await UpdateSprintUseCase(sprint_repo).execute(sprint.id, name="New Name")

    assert result.name == "New Name"
    saved = await sprint_repo.get_by_id(sprint.id)
    assert saved is not None
    assert saved.name == "New Name"


async def test_update_sprint_goal(
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Sprint G", _date_range())
    await sprint_repo.save(sprint)

    result = await UpdateSprintUseCase(sprint_repo).execute(sprint.id, goal="Zero downtime migration")

    assert result.goal == "Zero downtime migration"
    saved = await sprint_repo.get_by_id(sprint.id)
    assert saved is not None
    assert saved.goal == "Zero downtime migration"


async def test_update_sprint_name_and_goal_together(
    sprint_repo: InMemorySprintRepository,
) -> None:
    sprint = Sprint("Old", _date_range())
    await sprint_repo.save(sprint)

    result = await UpdateSprintUseCase(sprint_repo).execute(
        sprint.id, name="New", goal="New goal"
    )

    assert result.name == "New"
    assert result.goal == "New goal"


async def test_update_sprint_not_found_raises(
    sprint_repo: InMemorySprintRepository,
) -> None:
    with pytest.raises(ValueError):
        await UpdateSprintUseCase(sprint_repo).execute(uuid.uuid4(), name="X")


# ---------------------------------------------------------------------------
# DeleteSprintUseCase
# ---------------------------------------------------------------------------

async def test_delete_planned_sprint(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Planned", _date_range())
    await sprint_repo.save(sprint)

    await DeleteSprintUseCase(sprint_repo, event_bus).execute(sprint.id)

    assert await sprint_repo.get_by_id(sprint.id) is None


async def test_delete_sprint_publishes_deleted_event(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Planned", _date_range())
    await sprint_repo.save(sprint)

    spy = EventSpy()
    event_bus.subscribe(SprintDeletedEvent, spy)

    await DeleteSprintUseCase(sprint_repo, event_bus).execute(sprint.id)

    assert len(spy.events) == 1
    assert isinstance(spy.events[0], SprintDeletedEvent)
    assert spy.events[0].sprint_id == sprint.id


async def test_delete_active_sprint_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    sprint = Sprint("Active", _date_range())
    sprint.start()
    await sprint_repo.save(sprint)

    with pytest.raises(InvalidOperationError):
        await DeleteSprintUseCase(sprint_repo, event_bus).execute(sprint.id)


async def test_delete_sprint_not_found_raises(
    sprint_repo: InMemorySprintRepository,
    event_bus: InMemoryEventBus,
) -> None:
    with pytest.raises(ValueError):
        await DeleteSprintUseCase(sprint_repo, event_bus).execute(uuid.uuid4())


async def test_add_task_task_not_found_raises(
    sprint_repo: InMemorySprintRepository,
    task_repo: InMemoryTaskRepository,
) -> None:
    sprint = Sprint("Sprint 1", _date_range())
    await sprint_repo.save(sprint)

    use_case = AddTaskToSprintUseCase(sprint_repo, task_repo)
    with pytest.raises(ValueError):
        await use_case.execute(sprint.id, uuid.uuid4())
