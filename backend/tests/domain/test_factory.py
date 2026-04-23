import uuid
from datetime import date

import pytest

from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask
from src.domain.factory import ITaskFactory, TaskFactory
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus


@pytest.fixture
def factory() -> TaskFactory:
    return TaskFactory()


# --- create_daily ---

def test_create_daily_returns_daily_task(factory: TaskFactory) -> None:
    t = factory.create_daily("Write tests")
    assert isinstance(t, DailyTask)


def test_create_daily_defaults(factory: TaskFactory) -> None:
    t = factory.create_daily("Write tests")
    assert t.title == "Write tests"
    assert t.status == TaskStatus.BACKLOG
    assert t.priority == Priority.MEDIUM
    assert t.estimation is None
    assert t.tags == frozenset()
    assert t.scheduled_date is None
    assert isinstance(t.id, uuid.UUID)


def test_create_daily_unique_ids(factory: TaskFactory) -> None:
    assert factory.create_daily("A").id != factory.create_daily("A").id


def test_create_daily_with_scheduled_date(factory: TaskFactory) -> None:
    d = date(2026, 5, 1)
    t = factory.create_daily("Task", scheduled_date=d)
    assert t.scheduled_date == d


def test_create_daily_with_all_options(factory: TaskFactory) -> None:
    t = factory.create_daily(
        "Task",
        priority=Priority.HIGH,
        estimation=Estimation(3),
        tags=frozenset({Tag("urgent")}),
    )
    assert t.priority == Priority.HIGH
    assert t.estimation == Estimation(3)
    assert Tag("urgent") in t.tags


# --- create_sprint ---

def test_create_sprint_returns_sprint_task(factory: TaskFactory) -> None:
    t = factory.create_sprint("Implement login")
    assert isinstance(t, SprintTask)


def test_create_sprint_defaults(factory: TaskFactory) -> None:
    t = factory.create_sprint("Task")
    assert t.status == TaskStatus.BACKLOG
    assert t.sprint_id is None
    assert t.story_points is None


def test_create_sprint_unique_ids(factory: TaskFactory) -> None:
    assert factory.create_sprint("A").id != factory.create_sprint("A").id


def test_create_sprint_with_sprint_id(factory: TaskFactory) -> None:
    sid = uuid.uuid4()
    t = factory.create_sprint("Task", sprint_id=sid)
    assert t.sprint_id == sid


def test_create_sprint_story_points_via_estimation(factory: TaskFactory) -> None:
    t = factory.create_sprint("Task", estimation=Estimation(8))
    assert t.story_points == 8


# --- create_goal ---

def test_create_goal_returns_long_term_goal(factory: TaskFactory) -> None:
    t = factory.create_goal("Learn Rust")
    assert isinstance(t, LongTermGoal)


def test_create_goal_defaults(factory: TaskFactory) -> None:
    t = factory.create_goal("Goal")
    assert t.status == TaskStatus.BACKLOG
    assert t.date_range is None


def test_create_goal_unique_ids(factory: TaskFactory) -> None:
    assert factory.create_goal("A").id != factory.create_goal("A").id


def test_create_goal_with_date_range(factory: TaskFactory) -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 6, 30))
    t = factory.create_goal("Goal", date_range=dr)
    assert t.date_range == dr


# --- create_milestone ---

def test_create_milestone_returns_milestone(factory: TaskFactory) -> None:
    t = factory.create_milestone("v1.0 release")
    assert isinstance(t, Milestone)


def test_create_milestone_defaults(factory: TaskFactory) -> None:
    t = factory.create_milestone("M1")
    assert t.status == TaskStatus.BACKLOG
    assert t.due_date is None
    assert t.goal_id is None


def test_create_milestone_unique_ids(factory: TaskFactory) -> None:
    assert factory.create_milestone("A").id != factory.create_milestone("A").id


def test_create_milestone_with_due_date_and_goal_id(factory: TaskFactory) -> None:
    gid = uuid.uuid4()
    t = factory.create_milestone("M1", due_date=date(2026, 3, 31), goal_id=gid)
    assert t.due_date == date(2026, 3, 31)
    assert t.goal_id == gid


# --- ITaskFactory is abstract ---

def test_itask_factory_is_abstract() -> None:
    with pytest.raises(TypeError):
        ITaskFactory()  # type: ignore[abstract]


# --- created_at is set ---

def test_create_daily_created_at_set(factory: TaskFactory) -> None:
    t = factory.create_daily("Task")
    assert t.created_at is not None


def test_create_sprint_created_at_set(factory: TaskFactory) -> None:
    t = factory.create_sprint("Task")
    assert t.created_at is not None
