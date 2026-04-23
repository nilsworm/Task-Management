import uuid
from datetime import date, datetime, timezone

import pytest

from src.domain.events import (
    GoalProgressEvent,
    IDomainEvent,
    IEventBus,
    IEventHandler,
    InMemoryEventBus,
    SprintCompletedEvent,
    SprintStartedEvent,
    TaskCreatedEvent,
    TaskStatusChangedEvent,
    TaskUpdatedEvent,
)


# --- helpers ---

def _task_id() -> uuid.UUID:
    return uuid.uuid4()


# --- IDomainEvent base ---

def test_task_created_event_has_uuid() -> None:
    e = TaskCreatedEvent(_task_id(), "daily")
    assert isinstance(e.event_id, uuid.UUID)


def test_task_created_event_has_occurred_at() -> None:
    e = TaskCreatedEvent(_task_id(), "daily")
    assert isinstance(e.occurred_at, datetime)


def test_each_event_gets_unique_id() -> None:
    tid = _task_id()
    e1 = TaskCreatedEvent(tid, "daily")
    e2 = TaskCreatedEvent(tid, "daily")
    assert e1.event_id != e2.event_id


# --- event_type properties ---

def test_task_created_event_type() -> None:
    assert TaskCreatedEvent(_task_id(), "sprint").event_type == "task.created"


def test_task_updated_event_type() -> None:
    assert TaskUpdatedEvent(_task_id(), ["title"]).event_type == "task.updated"


def test_task_status_changed_event_type() -> None:
    e = TaskStatusChangedEvent(_task_id(), "backlog", "todo")
    assert e.event_type == "task.status_changed"


def test_sprint_started_event_type() -> None:
    e = SprintStartedEvent(uuid.uuid4(), date(2026, 5, 1))
    assert e.event_type == "sprint.started"


def test_sprint_completed_event_type() -> None:
    e = SprintCompletedEvent(uuid.uuid4(), datetime.now(timezone.utc))
    assert e.event_type == "sprint.completed"


def test_goal_progress_event_type() -> None:
    assert GoalProgressEvent(uuid.uuid4(), 50.0).event_type == "goal.progress"


# --- event fields ---

def test_task_created_fields() -> None:
    tid = _task_id()
    e = TaskCreatedEvent(tid, "milestone")
    assert e.task_id == tid
    assert e.task_type == "milestone"


def test_task_updated_changed_fields() -> None:
    tid = _task_id()
    e = TaskUpdatedEvent(tid, ["title", "priority"])
    assert e.task_id == tid
    assert e.changed_fields == ["title", "priority"]


def test_task_status_changed_fields() -> None:
    tid = _task_id()
    e = TaskStatusChangedEvent(tid, "backlog", "todo")
    assert e.old_status == "backlog"
    assert e.new_status == "todo"


def test_sprint_started_fields() -> None:
    sid = uuid.uuid4()
    d = date(2026, 5, 1)
    e = SprintStartedEvent(sid, d)
    assert e.sprint_id == sid
    assert e.start_date == d


def test_sprint_completed_fields() -> None:
    sid = uuid.uuid4()
    now = datetime.now(timezone.utc)
    e = SprintCompletedEvent(sid, now)
    assert e.sprint_id == sid
    assert e.completed_at == now


def test_goal_progress_fields() -> None:
    gid = uuid.uuid4()
    e = GoalProgressEvent(gid, 75.5)
    assert e.goal_id == gid
    assert e.progress_percent == 75.5


# --- GoalProgressEvent validation ---

def test_goal_progress_zero_valid() -> None:
    e = GoalProgressEvent(uuid.uuid4(), 0.0)
    assert e.progress_percent == 0.0


def test_goal_progress_hundred_valid() -> None:
    e = GoalProgressEvent(uuid.uuid4(), 100.0)
    assert e.progress_percent == 100.0


def test_goal_progress_below_zero_raises() -> None:
    with pytest.raises(ValueError, match="0.0"):
        GoalProgressEvent(uuid.uuid4(), -0.1)


def test_goal_progress_above_hundred_raises() -> None:
    with pytest.raises(ValueError, match="100.0"):
        GoalProgressEvent(uuid.uuid4(), 100.1)


# --- IDomainEvent / IEventBus / IEventHandler are abstract ---

def test_idomain_event_is_abstract() -> None:
    with pytest.raises(TypeError):
        IDomainEvent()  # type: ignore[abstract]


def test_ievent_bus_is_abstract() -> None:
    with pytest.raises(TypeError):
        IEventBus()  # type: ignore[abstract]


def test_ievent_handler_is_abstract() -> None:
    with pytest.raises(TypeError):
        IEventHandler()  # type: ignore[abstract]


# --- InMemoryEventBus ---

class _Collector(IEventHandler):
    def __init__(self) -> None:
        self.received: list[IDomainEvent] = []

    def handle(self, event: IDomainEvent) -> None:
        self.received.append(event)


def test_publish_without_handler_is_safe() -> None:
    bus = InMemoryEventBus()
    bus.publish(TaskCreatedEvent(_task_id(), "daily"))


def test_publish_calls_subscribed_handler() -> None:
    bus = InMemoryEventBus()
    collector = _Collector()
    bus.subscribe(TaskCreatedEvent, collector)

    event = TaskCreatedEvent(_task_id(), "sprint")
    bus.publish(event)

    assert len(collector.received) == 1
    assert collector.received[0] is event


def test_publish_calls_multiple_handlers() -> None:
    bus = InMemoryEventBus()
    c1, c2 = _Collector(), _Collector()
    bus.subscribe(TaskCreatedEvent, c1)
    bus.subscribe(TaskCreatedEvent, c2)

    bus.publish(TaskCreatedEvent(_task_id(), "daily"))

    assert len(c1.received) == 1
    assert len(c2.received) == 1


def test_handler_not_called_for_different_event_type() -> None:
    bus = InMemoryEventBus()
    collector = _Collector()
    bus.subscribe(TaskCreatedEvent, collector)

    bus.publish(TaskUpdatedEvent(_task_id(), ["title"]))

    assert collector.received == []


def test_publish_multiple_events_collected_in_order() -> None:
    bus = InMemoryEventBus()
    collector = _Collector()
    bus.subscribe(TaskCreatedEvent, collector)

    e1 = TaskCreatedEvent(_task_id(), "daily")
    e2 = TaskCreatedEvent(_task_id(), "sprint")
    bus.publish(e1)
    bus.publish(e2)

    assert collector.received == [e1, e2]


def test_separate_subscriptions_per_event_type() -> None:
    bus = InMemoryEventBus()
    created_collector = _Collector()
    updated_collector = _Collector()
    bus.subscribe(TaskCreatedEvent, created_collector)
    bus.subscribe(TaskUpdatedEvent, updated_collector)

    bus.publish(TaskCreatedEvent(_task_id(), "goal"))
    bus.publish(TaskUpdatedEvent(_task_id(), ["description"]))

    assert len(created_collector.received) == 1
    assert len(updated_collector.received) == 1
    assert isinstance(created_collector.received[0], TaskCreatedEvent)
    assert isinstance(updated_collector.received[0], TaskUpdatedEvent)
