import pytest
from datetime import date

from src.domain.value_objects import (
    BurndownPoint,
    DateRange,
    Estimation,
    Priority,
    Tag,
    TaskStatus,
)


# --- Priority ---

def test_priority_values() -> None:
    assert Priority.LOW.value == "low"
    assert Priority.MEDIUM.value == "medium"
    assert Priority.HIGH.value == "high"
    assert Priority.CRITICAL.value == "critical"


def test_priority_equality() -> None:
    assert Priority.HIGH == Priority.HIGH
    assert Priority.LOW != Priority.HIGH


def test_priority_hashable() -> None:
    assert len({Priority.LOW, Priority.LOW, Priority.HIGH}) == 2


# --- TaskStatus ---

def test_task_status_values() -> None:
    assert TaskStatus.BACKLOG.value == "backlog"
    assert TaskStatus.TODO.value == "todo"
    assert TaskStatus.IN_PROGRESS.value == "in_progress"
    assert TaskStatus.REVIEW.value == "review"
    assert TaskStatus.BLOCKED.value == "blocked"
    assert TaskStatus.DONE.value == "done"
    assert TaskStatus.CANCELLED.value == "cancelled"


def test_task_status_hashable() -> None:
    statuses = {TaskStatus.TODO, TaskStatus.DONE, TaskStatus.TODO}
    assert len(statuses) == 2


# --- Estimation ---

def test_estimation_valid() -> None:
    e = Estimation(story_points=5)
    assert e.story_points == 5


def test_estimation_boundary_min() -> None:
    assert Estimation(story_points=1).story_points == 1


def test_estimation_boundary_max() -> None:
    assert Estimation(story_points=100).story_points == 100


def test_estimation_too_low() -> None:
    with pytest.raises(ValueError, match=">= 1"):
        Estimation(story_points=0)


def test_estimation_too_high() -> None:
    with pytest.raises(ValueError, match="<= 100"):
        Estimation(story_points=101)


def test_estimation_equality() -> None:
    assert Estimation(3) == Estimation(3)
    assert Estimation(3) != Estimation(5)


def test_estimation_hashable() -> None:
    assert len({Estimation(3), Estimation(3), Estimation(5)}) == 2


def test_estimation_immutable() -> None:
    e = Estimation(story_points=3)
    with pytest.raises(Exception):
        e.story_points = 5  # type: ignore[misc]


# --- DateRange ---

def test_daterange_valid() -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    assert dr.start == date(2026, 1, 1)
    assert dr.end == date(2026, 1, 14)


def test_daterange_same_day() -> None:
    dr = DateRange(date(2026, 6, 1), date(2026, 6, 1))
    assert dr.duration_days == 1


def test_daterange_duration_days() -> None:
    dr = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    assert dr.duration_days == 14


def test_daterange_end_before_start_raises() -> None:
    with pytest.raises(ValueError, match="end must not be before start"):
        DateRange(date(2026, 1, 10), date(2026, 1, 5))


def test_daterange_equality() -> None:
    d1 = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    d2 = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    assert d1 == d2


def test_daterange_hashable() -> None:
    d1 = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    d2 = DateRange(date(2026, 1, 1), date(2026, 1, 14))
    assert len({d1, d2}) == 1


# --- Tag ---

def test_tag_valid() -> None:
    t = Tag("backend")
    assert t.name == "backend"


def test_tag_normalized_whitespace() -> None:
    t = Tag("  Backend  ")
    assert t.name == "backend"


def test_tag_normalized_uppercase() -> None:
    t = Tag("URGENT")
    assert t.name == "urgent"


def test_tag_empty_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        Tag("")


def test_tag_whitespace_only_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        Tag("   ")


def test_tag_too_long_raises() -> None:
    with pytest.raises(ValueError, match="50 characters"):
        Tag("a" * 51)


def test_tag_max_length_valid() -> None:
    t = Tag("a" * 50)
    assert len(t.name) == 50


def test_tag_equality() -> None:
    assert Tag("backend") == Tag("Backend")
    assert Tag("backend") != Tag("frontend")


def test_tag_hashable_normalized() -> None:
    assert len({Tag("Backend"), Tag("backend"), Tag("FRONTEND")}) == 2


# --- BurndownPoint ---

def test_burndown_point_valid() -> None:
    bp = BurndownPoint(date(2026, 1, 5), remaining_points=21)
    assert bp.date == date(2026, 1, 5)
    assert bp.remaining_points == 21


def test_burndown_point_zero_remaining() -> None:
    bp = BurndownPoint(date(2026, 1, 14), remaining_points=0)
    assert bp.remaining_points == 0


def test_burndown_point_negative_raises() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        BurndownPoint(date(2026, 1, 5), remaining_points=-1)


def test_burndown_point_equality() -> None:
    d = date(2026, 1, 5)
    assert BurndownPoint(d, 10) == BurndownPoint(d, 10)
    assert BurndownPoint(d, 10) != BurndownPoint(d, 5)


def test_burndown_point_hashable() -> None:
    d = date(2026, 1, 5)
    assert len({BurndownPoint(d, 10), BurndownPoint(d, 10)}) == 1
