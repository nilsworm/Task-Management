from __future__ import annotations

import uuid
from datetime import date

import pytest

from src.application.use_cases.task_use_cases import (
    UNSET,
    CreateTaskInput,
    CreateTaskUseCase,
    DeleteTaskUseCase,
    TransitionTaskUseCase,
    UpdateTaskInput,
    UpdateTaskUseCase,
)
from src.domain.events import (
    InMemoryEventBus,
    TaskCreatedEvent,
    TaskStatusChangedEvent,
    TaskUpdatedEvent,
)
from src.domain.factory import TaskFactory
from src.domain.value_objects import DateRange, Estimation, Priority, TaskStatus

from .conftest import EventSpy, InMemoryTaskRepository


# ---------------------------------------------------------------------------
# CreateTaskUseCase
# ---------------------------------------------------------------------------

async def test_create_daily_task_saves_and_returns(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    task = await use_case.execute(CreateTaskInput(task_type="daily", title="Morning run"))
    assert task.title == "Morning run"
    saved = await task_repo.get_by_id(task.id)
    assert saved is task


async def test_create_sprint_task_saves(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    sprint_id = uuid.uuid4()
    task = await use_case.execute(
        CreateTaskInput(task_type="sprint", title="Auth flow", sprint_id=sprint_id)
    )
    assert await task_repo.get_by_id(task.id) is task


async def test_create_goal_task_saves(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    dr = DateRange(date(2026, 5, 1), date(2026, 7, 31))
    task = await use_case.execute(
        CreateTaskInput(task_type="goal", title="Learn Rust", date_range=dr)
    )
    assert await task_repo.get_by_id(task.id) is task


async def test_create_milestone_saves(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    task = await use_case.execute(
        CreateTaskInput(
            task_type="milestone",
            title="Ship MVP",
            due_date=date(2026, 6, 30),
            goal_id=uuid.uuid4(),
        )
    )
    assert await task_repo.get_by_id(task.id) is task


async def test_create_task_publishes_created_event(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    spy = EventSpy()
    event_bus.subscribe(TaskCreatedEvent, spy)

    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    task = await use_case.execute(CreateTaskInput(task_type="daily", title="Write tests"))

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, TaskCreatedEvent)
    assert event.task_id == task.id
    assert event.task_type == "daily"


async def test_create_task_unknown_type_raises(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    with pytest.raises(ValueError, match="Unknown task_type"):
        await use_case.execute(CreateTaskInput(task_type="bogus", title="Nope"))


async def test_create_task_with_priority_and_estimation(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = CreateTaskUseCase(task_repo, factory, event_bus)
    task = await use_case.execute(
        CreateTaskInput(
            task_type="daily",
            title="High prio task",
            priority=Priority.HIGH,
            estimation=Estimation(5),
        )
    )
    assert task.priority is Priority.HIGH
    assert task.estimation == Estimation(5)


# ---------------------------------------------------------------------------
# UpdateTaskUseCase
# ---------------------------------------------------------------------------

async def test_update_title(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Old title")
    await task_repo.save(task)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    updated = await use_case.execute(UpdateTaskInput(task_id=task.id, title="New title"))

    assert updated.title == "New title"
    assert (await task_repo.get_by_id(task.id)).title == "New title"  # type: ignore[union-attr]


async def test_update_description(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    updated = await use_case.execute(
        UpdateTaskInput(task_id=task.id, description="Some description")
    )
    assert updated.description == "Some description"


async def test_update_priority(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    updated = await use_case.execute(
        UpdateTaskInput(task_id=task.id, priority=Priority.CRITICAL)
    )
    assert updated.priority is Priority.CRITICAL


async def test_update_estimation(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    updated = await use_case.execute(
        UpdateTaskInput(task_id=task.id, estimation=Estimation(8))
    )
    assert updated.estimation == Estimation(8)


async def test_update_publishes_event_with_changed_fields(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    spy = EventSpy()
    event_bus.subscribe(TaskUpdatedEvent, spy)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    await use_case.execute(UpdateTaskInput(task_id=task.id, title="New", priority=Priority.LOW))

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, TaskUpdatedEvent)
    assert set(event.changed_fields) == {"title", "priority"}


async def test_update_no_fields_no_event(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    spy = EventSpy()
    event_bus.subscribe(TaskUpdatedEvent, spy)

    use_case = UpdateTaskUseCase(task_repo, event_bus)
    await use_case.execute(UpdateTaskInput(task_id=task.id))

    assert len(spy.events) == 0


async def test_update_task_not_found_raises(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = UpdateTaskUseCase(task_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(UpdateTaskInput(task_id=uuid.uuid4(), title="x"))


# ---------------------------------------------------------------------------
# TransitionTaskUseCase
# ---------------------------------------------------------------------------

async def test_transition_task_changes_status(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = TransitionTaskUseCase(task_repo, event_bus)
    updated = await use_case.execute(task.id, TaskStatus.TODO)

    assert updated.status is TaskStatus.TODO
    assert (await task_repo.get_by_id(task.id)).status is TaskStatus.TODO  # type: ignore[union-attr]


async def test_transition_task_publishes_status_changed_event(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    spy = EventSpy()
    event_bus.subscribe(TaskStatusChangedEvent, spy)

    use_case = TransitionTaskUseCase(task_repo, event_bus)
    await use_case.execute(task.id, TaskStatus.TODO)

    assert len(spy.events) == 1
    event = spy.events[0]
    assert isinstance(event, TaskStatusChangedEvent)
    assert event.task_id == task.id
    assert event.old_status == TaskStatus.BACKLOG.value
    assert event.new_status == TaskStatus.TODO.value


async def test_transition_task_invalid_transition_raises(
    task_repo: InMemoryTaskRepository,
    factory: TaskFactory,
    event_bus: InMemoryEventBus,
) -> None:
    task = factory.create_daily("Task")
    await task_repo.save(task)

    use_case = TransitionTaskUseCase(task_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(task.id, TaskStatus.DONE)


async def test_transition_task_not_found_raises(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = TransitionTaskUseCase(task_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(uuid.uuid4(), TaskStatus.TODO)


# ---------------------------------------------------------------------------
# DeleteTaskUseCase
# ---------------------------------------------------------------------------

async def test_delete_task_removes_it(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
    factory: TaskFactory,
) -> None:
    task = factory.create_daily("Temp task")
    await task_repo.save(task)

    use_case = DeleteTaskUseCase(task_repo, event_bus)
    await use_case.execute(task.id)

    assert await task_repo.get_by_id(task.id) is None


async def test_delete_task_publishes_deleted_event(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
    factory: TaskFactory,
) -> None:
    from src.domain.events import TaskDeletedEvent

    task = factory.create_daily("Temp task")
    await task_repo.save(task)

    spy = EventSpy()
    event_bus.subscribe(TaskDeletedEvent, spy)

    await DeleteTaskUseCase(task_repo, event_bus).execute(task.id)

    assert len(spy.events) == 1
    assert isinstance(spy.events[0], TaskDeletedEvent)
    assert spy.events[0].task_id == task.id


async def test_delete_task_not_found_raises(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
) -> None:
    use_case = DeleteTaskUseCase(task_repo, event_bus)
    with pytest.raises(ValueError):
        await use_case.execute(uuid.uuid4())


# ---------------------------------------------------------------------------
# UpdateTaskUseCase — due_date sentinel
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_task_due_date_not_provided_leaves_unchanged(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
    factory: TaskFactory,
) -> None:
    task = factory.create_milestone("M", due_date=date(2026, 12, 31))
    await task_repo.save(task)
    updated = await UpdateTaskUseCase(task_repo, event_bus).execute(
        UpdateTaskInput(task_id=task.id, title="Updated")
    )
    from src.domain.entities import Milestone
    assert isinstance(updated, Milestone)
    assert updated.due_date == date(2026, 12, 31)


@pytest.mark.asyncio
async def test_update_task_due_date_explicit_none_clears_it(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
    factory: TaskFactory,
) -> None:
    task = factory.create_milestone("M", due_date=date(2026, 12, 31))
    await task_repo.save(task)
    updated = await UpdateTaskUseCase(task_repo, event_bus).execute(
        UpdateTaskInput(task_id=task.id, due_date=None)
    )
    from src.domain.entities import Milestone
    assert isinstance(updated, Milestone)
    assert updated.due_date is None


@pytest.mark.asyncio
async def test_update_task_due_date_unset_default(
    task_repo: InMemoryTaskRepository,
    event_bus: InMemoryEventBus,
    factory: TaskFactory,
) -> None:
    inp = UpdateTaskInput(task_id=uuid.uuid4())
    assert inp.due_date is UNSET
