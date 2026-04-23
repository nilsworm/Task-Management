from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.events import InMemoryEventBus
from src.infrastructure.database import get_session
from src.infrastructure.persistence.repositories.goal_repository import PostgresGoalRepository
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository
from src.infrastructure.persistence.repositories.task_repository import PostgresTaskRepository

# One event bus for the lifetime of the process
_event_bus = InMemoryEventBus()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_task_repo(session: SessionDep) -> PostgresTaskRepository:
    return PostgresTaskRepository(session)


def get_sprint_repo(session: SessionDep) -> PostgresSprintRepository:
    return PostgresSprintRepository(session)


def get_goal_repo(session: SessionDep) -> PostgresGoalRepository:
    return PostgresGoalRepository(session)


def get_event_bus() -> InMemoryEventBus:
    return _event_bus


TaskRepoDep = Annotated[PostgresTaskRepository, Depends(get_task_repo)]
SprintRepoDep = Annotated[PostgresSprintRepository, Depends(get_sprint_repo)]
GoalRepoDep = Annotated[PostgresGoalRepository, Depends(get_goal_repo)]
EventBusDep = Annotated[InMemoryEventBus, Depends(get_event_bus)]
