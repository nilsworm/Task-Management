import pytest

from src.domain.states import (
    BacklogState,
    BlockedState,
    CancelledState,
    DoneState,
    InProgressState,
    ITaskState,
    ReviewState,
    StateFactory,
    TodoState,
)
from src.domain.value_objects import TaskStatus


# --- BacklogState ---

def test_backlog_allows_todo() -> None:
    assert BacklogState().can_transition_to(TaskStatus.TODO) is True

def test_backlog_allows_cancelled() -> None:
    assert BacklogState().can_transition_to(TaskStatus.CANCELLED) is True

@pytest.mark.parametrize("status", [
    TaskStatus.BACKLOG, TaskStatus.IN_PROGRESS, TaskStatus.REVIEW,
    TaskStatus.BLOCKED, TaskStatus.DONE,
])
def test_backlog_disallows(status: TaskStatus) -> None:
    assert BacklogState().can_transition_to(status) is False


# --- TodoState ---

def test_todo_allows_in_progress() -> None:
    assert TodoState().can_transition_to(TaskStatus.IN_PROGRESS) is True

def test_todo_allows_backlog() -> None:
    assert TodoState().can_transition_to(TaskStatus.BACKLOG) is True

def test_todo_allows_cancelled() -> None:
    assert TodoState().can_transition_to(TaskStatus.CANCELLED) is True

@pytest.mark.parametrize("status", [
    TaskStatus.TODO, TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.DONE,
])
def test_todo_disallows(status: TaskStatus) -> None:
    assert TodoState().can_transition_to(status) is False


# --- InProgressState ---

def test_in_progress_allows_review() -> None:
    assert InProgressState().can_transition_to(TaskStatus.REVIEW) is True

def test_in_progress_allows_blocked() -> None:
    assert InProgressState().can_transition_to(TaskStatus.BLOCKED) is True

def test_in_progress_allows_todo() -> None:
    assert InProgressState().can_transition_to(TaskStatus.TODO) is True

def test_in_progress_allows_cancelled() -> None:
    assert InProgressState().can_transition_to(TaskStatus.CANCELLED) is True

@pytest.mark.parametrize("status", [
    TaskStatus.BACKLOG, TaskStatus.IN_PROGRESS, TaskStatus.DONE,
])
def test_in_progress_disallows(status: TaskStatus) -> None:
    assert InProgressState().can_transition_to(status) is False


# --- ReviewState ---

def test_review_allows_done() -> None:
    assert ReviewState().can_transition_to(TaskStatus.DONE) is True

def test_review_allows_in_progress() -> None:
    assert ReviewState().can_transition_to(TaskStatus.IN_PROGRESS) is True

def test_review_allows_cancelled() -> None:
    assert ReviewState().can_transition_to(TaskStatus.CANCELLED) is True

@pytest.mark.parametrize("status", [
    TaskStatus.BACKLOG, TaskStatus.TODO, TaskStatus.BLOCKED, TaskStatus.REVIEW,
])
def test_review_disallows(status: TaskStatus) -> None:
    assert ReviewState().can_transition_to(status) is False


# --- BlockedState ---

def test_blocked_allows_todo() -> None:
    assert BlockedState().can_transition_to(TaskStatus.TODO) is True

def test_blocked_allows_in_progress() -> None:
    assert BlockedState().can_transition_to(TaskStatus.IN_PROGRESS) is True

def test_blocked_allows_cancelled() -> None:
    assert BlockedState().can_transition_to(TaskStatus.CANCELLED) is True

@pytest.mark.parametrize("status", [
    TaskStatus.BACKLOG, TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.DONE,
])
def test_blocked_disallows(status: TaskStatus) -> None:
    assert BlockedState().can_transition_to(status) is False


# --- DoneState ---

@pytest.mark.parametrize("status", list(TaskStatus))
def test_done_disallows_all(status: TaskStatus) -> None:
    assert DoneState().can_transition_to(status) is False


# --- CancelledState ---

@pytest.mark.parametrize("status", list(TaskStatus))
def test_cancelled_disallows_all(status: TaskStatus) -> None:
    assert CancelledState().can_transition_to(status) is False


# --- StateFactory ---

@pytest.mark.parametrize("status,expected_cls", [
    (TaskStatus.BACKLOG, BacklogState),
    (TaskStatus.TODO, TodoState),
    (TaskStatus.IN_PROGRESS, InProgressState),
    (TaskStatus.REVIEW, ReviewState),
    (TaskStatus.BLOCKED, BlockedState),
    (TaskStatus.DONE, DoneState),
    (TaskStatus.CANCELLED, CancelledState),
])
def test_state_factory_returns_correct_type(
    status: TaskStatus, expected_cls: type[ITaskState]
) -> None:
    state = StateFactory.for_status(status)
    assert isinstance(state, expected_cls)


def test_state_factory_covers_all_statuses() -> None:
    for status in TaskStatus:
        state = StateFactory.for_status(status)
        assert isinstance(state, ITaskState)


# --- on_enter hook ---

def test_on_enter_is_callable_without_error() -> None:
    for status in TaskStatus:
        state = StateFactory.for_status(status)
        state.on_enter(None)  # type: ignore[arg-type]
