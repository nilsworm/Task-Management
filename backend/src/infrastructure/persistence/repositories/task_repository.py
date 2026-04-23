from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import SprintTask, Task
from src.domain.repositories.task_repository import ITaskRepository
from src.domain.value_objects import TaskStatus
from src.infrastructure.persistence.mappers import task_from_model, task_to_model
from src.infrastructure.persistence.models.task_model import TaskModel


class PostgresTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, task_id: uuid.UUID) -> Task | None:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        model = result.scalar_one_or_none()
        return task_from_model(model) if model else None

    async def save(self, task: Task) -> None:
        model = task_to_model(task)
        await self._session.merge(model)
        await self._session.commit()

    async def delete(self, task_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(TaskModel).where(TaskModel.id == task_id)
        )
        await self._session.commit()

    async def list_all(self) -> list[Task]:
        result = await self._session.execute(select(TaskModel))
        return [task_from_model(m) for m in result.scalars().all()]

    async def list_by_status(self, status: TaskStatus) -> list[Task]:
        result = await self._session.execute(
            select(TaskModel).where(TaskModel.status == status.value)
        )
        return [task_from_model(m) for m in result.scalars().all()]

    async def list_by_sprint(
        self,
        sprint_id: uuid.UUID,
        status_filter: TaskStatus | None = None,
    ) -> list[SprintTask]:
        conditions = [
            TaskModel.task_type == "sprint",
            TaskModel.sprint_id == sprint_id,
        ]
        if status_filter is not None:
            conditions.append(TaskModel.status == status_filter.value)
        result = await self._session.execute(select(TaskModel).where(*conditions))
        tasks = [task_from_model(m) for m in result.scalars().all()]
        return [t for t in tasks if isinstance(t, SprintTask)]
