"""Tests for Domain <-> DTO mapping (from_domain / to_use_case_input)."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

import pytest

from src.api.schemas.goal_schemas import GoalCreateRequest, GoalResponse
from src.api.schemas.sprint_schemas import SprintCreateRequest, SprintResponse
from src.api.schemas.task_schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskTransitionRequest,
    TaskUpdateRequest,
)
from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask
from src.domain.factory import TaskFactory
from src.domain.sprint import Sprint, SprintStatus
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus


_factory = TaskFactory()
_now = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)
_dr = DateRange(date(2026, 5, 1), date(2026, 5, 14))


# ---------------------------------------------------------------------------
# TaskResponse.from_domain
# ---------------------------------------------------------------------------

def test_task_response_from_daily_task() -> None:
    task = _factory.create_daily(
        "Morning standup",
        scheduled_date=date(2026, 5, 3),
        priority=Priority.HIGH,
        estimation=Estimation(3),
        tags=frozenset({Tag("backend")}),
    )
    resp = TaskResponse.from_domain(task)

    assert resp.id == task.id
    assert resp.task_type == "daily"
    assert resp.title == "Morning standup"
    assert resp.status == "backlog"
    assert resp.priority == "high"
    assert resp.estimation == 3
    assert resp.tags == ["backend"]
    assert resp.scheduled_date == date(2026, 5, 3)
    assert resp.sprint_id is None
    assert resp.date_range_start is None
    assert resp.date_range_end is None
    assert resp.due_date is None
    assert resp.goal_id is None


def test_task_response_from_sprint_task() -> None:
    sid = uuid.uuid4()
    task = _factory.create_sprint("Auth endpoint", sprint_id=sid, estimation=Estimation(5))
    resp = TaskResponse.from_domain(task)

    assert resp.task_type == "sprint"
    assert resp.sprint_id == sid
    assert resp.estimation == 5
    assert resp.scheduled_date is None


def test_task_response_from_long_term_goal() -> None:
    task = _factory.create_goal("Learn Rust", date_range=_dr)
    resp = TaskResponse.from_domain(task)

    assert resp.task_type == "goal"
    assert resp.date_range_start == date(2026, 5, 1)
    assert resp.date_range_end == date(2026, 5, 14)
    assert resp.sprint_id is None


def test_task_response_from_milestone() -> None:
    gid = uuid.uuid4()
    task = _factory.create_milestone("Ship MVP", due_date=date(2026, 6, 30), goal_id=gid)
    resp = TaskResponse.from_domain(task)

    assert resp.task_type == "milestone"
    assert resp.due_date == date(2026, 6, 30)
    assert resp.goal_id == gid


def test_task_response_tags_sorted() -> None:
    task = _factory.create_daily(
        "Task", tags=frozenset({Tag("zebra"), Tag("apple"), Tag("mango")})
    )
    resp = TaskResponse.from_domain(task)
    assert resp.tags == ["apple", "mango", "zebra"]


def test_task_response_no_estimation() -> None:
    task = _factory.create_daily("No estimate")
    assert TaskResponse.from_domain(task).estimation is None


# ---------------------------------------------------------------------------
# TaskCreateRequest.to_use_case_input
# ---------------------------------------------------------------------------

def test_task_create_request_daily_to_input() -> None:
    req = TaskCreateRequest(
        task_type="daily",
        title="Do laundry",
        priority="high",
        estimation=3,
        tags=["home"],
        scheduled_date=date(2026, 5, 2),
    )
    inp = req.to_use_case_input()

    assert inp.task_type == "daily"
    assert inp.title == "Do laundry"
    assert inp.priority == Priority.HIGH
    assert inp.estimation == Estimation(3)
    assert Tag("home") in inp.tags
    assert inp.scheduled_date == date(2026, 5, 2)


def test_task_create_request_goal_with_date_range() -> None:
    req = TaskCreateRequest(
        task_type="goal",
        title="Learn Rust",
        date_range_start=date(2026, 5, 1),
        date_range_end=date(2026, 7, 31),
    )
    inp = req.to_use_case_input()

    assert inp.date_range == DateRange(date(2026, 5, 1), date(2026, 7, 31))


def test_task_create_request_no_estimation() -> None:
    req = TaskCreateRequest(task_type="daily", title="Quick task")
    assert req.to_use_case_input().estimation is None


def test_task_create_request_tags_to_frozenset() -> None:
    req = TaskCreateRequest(task_type="daily", title="Tagged", tags=["backend", "urgent"])
    inp = req.to_use_case_input()
    assert isinstance(inp.tags, frozenset)
    assert Tag("backend") in inp.tags
    assert Tag("urgent") in inp.tags


# ---------------------------------------------------------------------------
# TaskUpdateRequest.to_use_case_input
# ---------------------------------------------------------------------------

def test_task_update_request_to_input() -> None:
    tid = uuid.uuid4()
    req = TaskUpdateRequest(title="Updated", priority="critical", estimation=8)
    inp = req.to_use_case_input(tid)

    assert inp.task_id == tid
    assert inp.title == "Updated"
    assert inp.priority == Priority.CRITICAL
    assert inp.estimation == Estimation(8)


def test_task_update_request_all_none() -> None:
    tid = uuid.uuid4()
    inp = TaskUpdateRequest().to_use_case_input(tid)
    assert inp.title is None
    assert inp.priority is None
    assert inp.estimation is None


# ---------------------------------------------------------------------------
# TaskTransitionRequest
# ---------------------------------------------------------------------------

def test_task_transition_request_to_status() -> None:
    req = TaskTransitionRequest(status="in_progress")
    assert req.to_task_status() == TaskStatus.IN_PROGRESS


def test_task_transition_request_invalid_status() -> None:
    with pytest.raises(Exception):
        TaskTransitionRequest(status="flying")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# SprintResponse.from_domain
# ---------------------------------------------------------------------------

def test_sprint_response_from_domain() -> None:
    sprint = Sprint("Sprint 1", _dr)
    sprint.start()
    t1, t2 = uuid.uuid4(), uuid.uuid4()
    sprint.add_task(t1)
    sprint.add_task(t2)

    resp = SprintResponse.from_domain(sprint)

    assert resp.id == sprint.id
    assert resp.name == "Sprint 1"
    assert resp.status == "active"
    assert resp.start_date == date(2026, 5, 1)
    assert resp.end_date == date(2026, 5, 14)
    assert set(resp.task_ids) == {t1, t2}


def test_sprint_response_planned_status() -> None:
    resp = SprintResponse.from_domain(Sprint("S", _dr))
    assert resp.status == "planned"


# ---------------------------------------------------------------------------
# SprintCreateRequest
# ---------------------------------------------------------------------------

def test_sprint_create_request_to_date_range() -> None:
    req = SprintCreateRequest(
        name="Sprint 1", start_date=date(2026, 5, 1), end_date=date(2026, 5, 14)
    )
    dr = req.to_date_range()
    assert dr.start == date(2026, 5, 1)
    assert dr.end == date(2026, 5, 14)


def test_sprint_create_request_invalid_date_range() -> None:
    req = SprintCreateRequest(
        name="Bad Sprint", start_date=date(2026, 5, 14), end_date=date(2026, 5, 1)
    )
    with pytest.raises(ValueError):
        req.to_date_range()  # DateRange validates end >= start


# ---------------------------------------------------------------------------
# GoalResponse.from_domain
# ---------------------------------------------------------------------------

def test_goal_response_from_domain() -> None:
    goal = LongTermGoal(
        "Master FastAPI",
        description="Deep dive",
        priority=Priority.HIGH,
        tags=frozenset({Tag("python"), Tag("backend")}),
        date_range=_dr,
    )
    resp = GoalResponse.from_domain(goal)

    assert resp.id == goal.id
    assert resp.title == "Master FastAPI"
    assert resp.description == "Deep dive"
    assert resp.priority == "high"
    assert resp.tags == ["backend", "python"]
    assert resp.date_range_start == date(2026, 5, 1)
    assert resp.date_range_end == date(2026, 5, 14)


def test_goal_response_no_date_range() -> None:
    goal = LongTermGoal("Simple goal")
    resp = GoalResponse.from_domain(goal)
    assert resp.date_range_start is None
    assert resp.date_range_end is None


# ---------------------------------------------------------------------------
# GoalCreateRequest.to_domain
# ---------------------------------------------------------------------------

def test_goal_create_request_to_domain() -> None:
    req = GoalCreateRequest(
        title="Learn Rust",
        description="Systems programming",
        priority="high",
        tags=["rust", "systems"],
        date_range_start=date(2026, 5, 1),
        date_range_end=date(2026, 7, 31),
    )
    goal = req.to_domain()

    assert goal.title == "Learn Rust"
    assert goal.description == "Systems programming"
    assert goal.priority == Priority.HIGH
    assert Tag("rust") in goal.tags
    assert goal.date_range == DateRange(date(2026, 5, 1), date(2026, 7, 31))
    assert isinstance(goal.id, uuid.UUID)


def test_goal_create_request_minimal() -> None:
    req = GoalCreateRequest(title="Minimal goal")
    goal = req.to_domain()
    assert goal.date_range is None
    assert goal.tags == frozenset()
