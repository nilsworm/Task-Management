from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.value_objects import TaskStatus

if TYPE_CHECKING:
    from src.domain.entities import Task


class ITaskState(ABC):
    @abstractmethod
    def can_transition_to(self, next_status: TaskStatus) -> bool: ...

    def on_enter(self, task: Task) -> None:
        pass


class BacklogState(ITaskState):
    _allowed = frozenset({TaskStatus.TODO, TaskStatus.CANCELLED})

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return next_status in self._allowed


class TodoState(ITaskState):
    _allowed = frozenset({TaskStatus.IN_PROGRESS, TaskStatus.BACKLOG, TaskStatus.CANCELLED})

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return next_status in self._allowed


class InProgressState(ITaskState):
    _allowed = frozenset({TaskStatus.REVIEW, TaskStatus.BLOCKED, TaskStatus.TODO, TaskStatus.CANCELLED})

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return next_status in self._allowed


class ReviewState(ITaskState):
    _allowed = frozenset({TaskStatus.DONE, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED})

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return next_status in self._allowed


class BlockedState(ITaskState):
    _allowed = frozenset({TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED})

    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return next_status in self._allowed


class DoneState(ITaskState):
    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return False


class CancelledState(ITaskState):
    def can_transition_to(self, next_status: TaskStatus) -> bool:
        return False


_STATUS_TO_STATE: dict[TaskStatus, type[ITaskState]] = {
    TaskStatus.BACKLOG: BacklogState,
    TaskStatus.TODO: TodoState,
    TaskStatus.IN_PROGRESS: InProgressState,
    TaskStatus.REVIEW: ReviewState,
    TaskStatus.BLOCKED: BlockedState,
    TaskStatus.DONE: DoneState,
    TaskStatus.CANCELLED: CancelledState,
}


class StateFactory:
    @staticmethod
    def for_status(status: TaskStatus) -> ITaskState:
        return _STATUS_TO_STATE[status]()
