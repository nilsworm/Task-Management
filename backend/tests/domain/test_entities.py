import uuid
from datetime import date, datetime, timezone

import pytest

from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask, Task
from src.domain.value_objects import (
    DateRange,
    Estimation,
    Priority,
    Tag,
    TaskStatus,
)


# --- helpers ---

def make_daily(**kwargs) -> DailyTask:
    return DailyTask("Test task", **kwargs)

def make_sprint(**kwargs) -> SprintTask:
    return SprintTask("Test task", **kwargs)


# --- Task base: construction ---

def test_task_defaults() -> None:
    t = make_daily()
    assert t.title == "Test task"
    assert t.description == ""
    assert t.status == TaskStatus.BACKLOG
    assert t.priority == Priority.MEDIUM
    assert t.estimation is None
    assert t.tags == frozenset()
    assert isinstance(t.id, uuid.UUID)
    assert isinstance(t.created_at, datetime)
    assert isinstance(t.updated_at, datetime)


def test_task_explicit_id() -> None:
    fixed_id = uuid.uuid4()
    t = make_daily(id=fixed_id)
    assert t.id == fixed_id


def test_task_explicit_fields() -> None:
    t = make_daily(
        priority=Priority.HIGH,
        estimation=Estimation(8),
        tags=frozenset({Tag("backend")}),
        description="some desc",
    )
    assert t.priority == Priority.HIGH
    assert t.estimation == Estimation(8)
    assert Tag("backend") in t.tags
    assert t.description == "some desc"


# --- Task base: title validation ---

def test_task_empty_title_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        DailyTask("")


def test_task_whitespace_title_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        DailyTask("   ")


def test_task_title_too_long_raises() -> None:
    with pytest.raises(ValueError, match="200"):
        DailyTask("x" * 201)


def test_task_title_max_length_valid() -> None:
    t = DailyTask("x" * 200)
    assert len(t.title) == 200


# --- transition_to ---

def test_transition_allowed() -> None:
    t = make_daily()
    t.transition_to(TaskStatus.TODO)
    assert t.status == TaskStatus.TODO


def test_transition_chain() -> None:
    t = make_daily()
    t.transition_to(TaskStatus.TODO)
    t.transition_to(TaskStatus.IN_PROGRESS)
    t.transition_to(TaskStatus.REVIEW)
    t.transition_to(TaskStatus.DONE)
    assert t.status == TaskStatus.DONE


def test_transition_disallowed_raises() -> None:
    t = make_daily()
    with pytest.raises(ValueError, match="backlog.*done"):
        t.transition_to(TaskStatus.DONE)


def test_transition_disallowed_message() -> None:
    t = make_daily(status=TaskStatus.DONE)
    with pytest.raises(ValueError, match="done"):
        t.transition_to(TaskStatus.TODO)


def test_transition_updates_updated_at() -> None:
    t = make_daily()
    before = t.updated_at
    t.transition_to(TaskStatus.TODO)
    assert t.updated_at >= before


# --- add_tag / remove_tag ---

def test_add_tag() -> None:
    t = make_daily()
    t.add_tag(Tag("backend"))
    assert Tag("backend") in t.tags


def test_add_tag_is_idempotent() -> None:
    t = make_daily()
    t.add_tag(Tag("backend"))
    t.add_tag(Tag("backend"))
    assert len(t.tags) == 1


def test_remove_tag() -> None:
    t = make_daily(tags=frozenset({Tag("backend"), Tag("urgent")}))
    t.remove_tag(Tag("backend"))
    assert Tag("backend") not in t.tags
    assert Tag("urgent") in t.tags


def test_remove_nonexistent_tag_is_safe() -> None:
    t = make_daily()
    t.remove_tag(Tag("nonexistent"))
    assert t.tags == frozenset()


# --- update_* mutators ---

def test_update_title() -> None:
    t = make_daily()
    t.update_title("New title")
    assert t.title == "New title"


def test_update_title_empty_raises() -> None:
    t = make_daily()
    with pytest.raises(ValueError, match="empty"):
        t.update_title("")


def test_update_description() -> None:
    t = make_daily()
    t.update_description("details")
    assert t.description == "details"


def test_update_priority() -> None:
    t = make_daily()
    t.update_priority(Priority.CRITICAL)
    assert t.priority == Priority.CRITICAL


def test_set_estimation() -> None:
    t = make_daily()
    t.set_estimation(Estimation(5))
    assert t.estimation == Estimation(5)


def test_set_estimation_none() -> None:
    t = make_daily(estimation=Estimation(3))
    t.set_estimation(None)
    assert t.estimation is None


# --- task_type ---

def test_task_type_daily() -> None:
    assert make_daily().task_type == "daily"


def test_task_type_sprint() -> None:
    assert make_sprint().task_type == "sprint"


def test_task_type_goal() -> None:
    assert LongTermGoal("Goal").task_type == "goal"


def test_task_type_milestone() -> None:
    assert Milestone("Milestone").task_type == "milestone"


# --- DailyTask ---

def test_daily_task_scheduled_date() -> None:
    d = date(2026, 5, 1)
    t = DailyTask("Task", scheduled_date=d)
    assert t.scheduled_date == d


def test_daily_task_no_scheduled_date() -> None:
    t = DailyTask("Task")
    assert t.scheduled_date is None


# --- SprintTask ---

def test_sprint_task_sprint_id() -> None:
    sid = uuid.uuid4()
    t = SprintTask("Task", sprint_id=sid)
    assert t.sprint_id == sid


def test_sprint_task_story_points_from_estimation() -> None:
    t = SprintTask("Task", estimation=Estimation(8))
    assert t.story_points == 8


def test_sprint_task_story_points_none_without_estimation() -> None:
    t = SprintTask("Task")
    assert t.story_points is None


# --- LongTermGoal ---

def test_long_term_goal_date_range() -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 6, 30))
    t = LongTermGoal("Goal", date_range=dr)
    assert t.date_range == dr


# --- Milestone ---

def test_milestone_due_date_and_goal_id() -> None:
    gid = uuid.uuid4()
    t = Milestone("M1", due_date=date(2026, 3, 31), goal_id=gid)
    assert t.due_date == date(2026, 3, 31)
    assert t.goal_id == gid


def test_milestone_defaults() -> None:
    t = Milestone("M1")
    assert t.due_date is None
    assert t.goal_id is None


# --- Task is abstract ---

def test_task_is_abstract() -> None:
    with pytest.raises(TypeError):
        Task("direct")  # type: ignore[abstract]
