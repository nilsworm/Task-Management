from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from src.domain.entities import DailyTask, LongTermGoal, Milestone, SprintTask
from src.domain.value_objects import DateRange, Estimation, Priority, Tag, TaskStatus

import uuid


class ITaskFactory(ABC):
    @abstractmethod
    def create_daily(
        self,
        title: str,
        *,
        scheduled_date: date | None = None,
        priority: Priority = Priority.MEDIUM,
        estimation: Estimation | None = None,
        tags: frozenset[Tag] | None = None,
    ) -> DailyTask: ...

    @abstractmethod
    def create_sprint(
        self,
        title: str,
        *,
        sprint_id: uuid.UUID | None = None,
        priority: Priority = Priority.MEDIUM,
        estimation: Estimation | None = None,
        tags: frozenset[Tag] | None = None,
    ) -> SprintTask: ...

    @abstractmethod
    def create_goal(
        self,
        title: str,
        *,
        date_range: DateRange | None = None,
        priority: Priority = Priority.MEDIUM,
        tags: frozenset[Tag] | None = None,
    ) -> LongTermGoal: ...

    @abstractmethod
    def create_milestone(
        self,
        title: str,
        *,
        due_date: date | None = None,
        goal_id: uuid.UUID | None = None,
        priority: Priority = Priority.MEDIUM,
        tags: frozenset[Tag] | None = None,
    ) -> Milestone: ...


class TaskFactory(ITaskFactory):
    def create_daily(
        self,
        title: str,
        *,
        scheduled_date: date | None = None,
        priority: Priority = Priority.MEDIUM,
        estimation: Estimation | None = None,
        tags: frozenset[Tag] | None = None,
    ) -> DailyTask:
        return DailyTask(
            title,
            scheduled_date=scheduled_date,
            status=TaskStatus.BACKLOG,
            priority=priority,
            estimation=estimation,
            tags=tags or frozenset(),
        )

    def create_sprint(
        self,
        title: str,
        *,
        sprint_id: uuid.UUID | None = None,
        priority: Priority = Priority.MEDIUM,
        estimation: Estimation | None = None,
        tags: frozenset[Tag] | None = None,
    ) -> SprintTask:
        return SprintTask(
            title,
            sprint_id=sprint_id,
            status=TaskStatus.BACKLOG,
            priority=priority,
            estimation=estimation,
            tags=tags or frozenset(),
        )

    def create_goal(
        self,
        title: str,
        *,
        date_range: DateRange | None = None,
        priority: Priority = Priority.MEDIUM,
        tags: frozenset[Tag] | None = None,
    ) -> LongTermGoal:
        return LongTermGoal(
            title,
            date_range=date_range,
            status=TaskStatus.BACKLOG,
            priority=priority,
            tags=tags or frozenset(),
        )

    def create_milestone(
        self,
        title: str,
        *,
        due_date: date | None = None,
        goal_id: uuid.UUID | None = None,
        priority: Priority = Priority.MEDIUM,
        tags: frozenset[Tag] | None = None,
    ) -> Milestone:
        return Milestone(
            title,
            due_date=due_date,
            goal_id=goal_id,
            status=TaskStatus.BACKLOG,
            priority=priority,
            tags=tags or frozenset(),
        )
