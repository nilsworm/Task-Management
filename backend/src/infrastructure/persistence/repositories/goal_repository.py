from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import KeyResult, LongTermGoal
from src.domain.repositories.goal_repository import IGoalRepository
from src.infrastructure.persistence.mappers import (
    goal_from_model,
    goal_to_model,
    key_result_from_model,
    key_result_to_model,
)
from src.infrastructure.persistence.models.goal_model import GoalModel, KeyResultModel


class PostgresGoalRepository(IGoalRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, goal_id: uuid.UUID) -> LongTermGoal | None:
        result = await self._session.execute(
            select(GoalModel).where(GoalModel.id == goal_id)
        )
        model = result.scalar_one_or_none()
        return goal_from_model(model) if model else None

    async def save(self, goal: LongTermGoal) -> None:
        model = goal_to_model(goal)
        await self._session.merge(model)
        await self._session.commit()

    async def delete(self, goal_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(GoalModel).where(GoalModel.id == goal_id)
        )
        await self._session.commit()

    async def list_all(self) -> list[LongTermGoal]:
        result = await self._session.execute(select(GoalModel))
        return [goal_from_model(m) for m in result.scalars().all()]

    async def list_key_results(self, goal_id: uuid.UUID) -> list[KeyResult]:
        result = await self._session.execute(
            select(KeyResultModel).where(KeyResultModel.goal_id == goal_id)
        )
        return [key_result_from_model(m) for m in result.scalars().all()]

    async def list_all_key_results(self) -> list[KeyResult]:
        result = await self._session.execute(select(KeyResultModel))
        return [key_result_from_model(m) for m in result.scalars().all()]

    async def get_key_result(self, key_result_id: uuid.UUID) -> KeyResult | None:
        result = await self._session.execute(
            select(KeyResultModel).where(KeyResultModel.id == key_result_id)
        )
        model = result.scalar_one_or_none()
        return key_result_from_model(model) if model else None

    async def save_key_result(self, key_result: KeyResult) -> None:
        model = key_result_to_model(key_result)
        await self._session.merge(model)
        await self._session.commit()

    async def delete_key_result(self, key_result_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(KeyResultModel).where(KeyResultModel.id == key_result_id)
        )
        await self._session.commit()
