from __future__ import annotations

import uuid

from sqlalchemy import delete, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.sprint import Sprint, SprintStatus
from src.infrastructure.persistence.mappers import sprint_from_model, sprint_to_model
from src.infrastructure.persistence.models.sprint_model import SprintModel
from src.infrastructure.persistence.models.task_model import TaskModel


class PostgresSprintRepository(ISprintRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, sprint_id: uuid.UUID) -> Sprint | None:
        result = await self._session.execute(
            select(SprintModel).where(SprintModel.id == sprint_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        task_ids = await self._load_task_ids(sprint_id)
        return sprint_from_model(model, task_ids)

    async def save(self, sprint: Sprint) -> None:
        model = sprint_to_model(sprint)
        await self._session.merge(model)
        await self._session.commit()

    async def delete(self, sprint_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(SprintModel).where(SprintModel.id == sprint_id)
        )
        await self._session.commit()

    async def list_all(self) -> list[Sprint]:
        result = await self._session.execute(select(SprintModel))
        models = result.scalars().all()
        if not models:
            return []
        task_id_map = await self._load_task_ids_bulk([m.id for m in models])
        return [sprint_from_model(m, task_id_map.get(m.id, [])) for m in models]

    async def get_active(self) -> Sprint | None:
        result = await self._session.execute(
            select(SprintModel).where(SprintModel.status == SprintStatus.ACTIVE.value)
        )
        model = result.scalar_one_or_none()
        if model is None:
            return None
        task_ids = await self._load_task_ids(model.id)
        return sprint_from_model(model, task_ids)

    async def _load_task_ids(self, sprint_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self._session.execute(
            select(TaskModel.id).where(
                TaskModel.sprint_id == sprint_id,
                TaskModel.task_type == "sprint",
            )
        )
        return list(result.scalars().all())

    async def _load_task_ids_bulk(
        self, sprint_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, list[uuid.UUID]]:
        result = await self._session.execute(
            select(TaskModel.id, TaskModel.sprint_id).where(
                TaskModel.sprint_id.in_(sprint_ids),
                TaskModel.task_type == "sprint",
            )
        )
        mapping: dict[uuid.UUID, list[uuid.UUID]] = {}
        for task_id, sprint_id in result.all():
            mapping.setdefault(sprint_id, []).append(task_id)
        return mapping
