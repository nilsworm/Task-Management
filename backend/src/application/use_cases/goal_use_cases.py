from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from src.application.exceptions import EntityNotFoundError
from src.domain.entities import KeyResult, LongTermGoal
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.value_objects import DateRange, Priority, Tag


@dataclass
class UpdateGoalInput:
    goal_id: uuid.UUID
    title: str | None = None
    description: str | None = None
    priority: Priority | None = None
    tags: frozenset[Tag] | None = None
    date_range: DateRange | None = None


class CreateGoalUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, goal: LongTermGoal) -> LongTermGoal:
        await self._repo.save(goal)
        return goal


class UpdateGoalUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, input: UpdateGoalInput) -> LongTermGoal:
        goal = await self._repo.get_by_id(input.goal_id)
        if goal is None:
            raise EntityNotFoundError("Goal", str(input.goal_id))
        if input.title is not None:
            goal.update_title(input.title)
        if input.description is not None:
            goal.update_description(input.description)
        if input.priority is not None:
            goal.update_priority(input.priority)
        if input.tags is not None:
            goal.tags = input.tags
        if input.date_range is not None:
            goal.date_range = input.date_range
        await self._repo.save(goal)
        return goal


class DeleteGoalUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, goal_id: uuid.UUID) -> None:
        goal = await self._repo.get_by_id(goal_id)
        if goal is None:
            raise EntityNotFoundError("Goal", str(goal_id))
        await self._repo.delete(goal_id)


@dataclass
class CreateKeyResultInput:
    goal_id: uuid.UUID
    title: str
    description: str = ""
    target_value: float = 1.0
    current_value: float = 0.0
    unit: str = ""


class CreateKeyResultUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, input: CreateKeyResultInput) -> KeyResult:
        goal = await self._repo.get_by_id(input.goal_id)
        if goal is None:
            raise EntityNotFoundError("Goal", str(input.goal_id))
        now = datetime.now(timezone.utc)
        kr = KeyResult(
            id=uuid.uuid4(),
            goal_id=input.goal_id,
            title=input.title,
            description=input.description,
            target_value=input.target_value,
            current_value=input.current_value,
            unit=input.unit,
            created_at=now,
            updated_at=now,
        )
        await self._repo.save_key_result(kr)
        return kr


@dataclass
class UpdateKeyResultInput:
    key_result_id: uuid.UUID
    title: str | None = None
    description: str | None = None
    current_value: float | None = None
    target_value: float | None = None
    unit: str | None = None


class UpdateKeyResultUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, input: UpdateKeyResultInput) -> KeyResult:
        kr = await self._repo.get_key_result(input.key_result_id)
        if kr is None:
            raise EntityNotFoundError("KeyResult", str(input.key_result_id))
        if input.title is not None:
            kr.title = input.title
        if input.description is not None:
            kr.description = input.description
        if input.current_value is not None:
            kr.current_value = input.current_value
        if input.target_value is not None:
            kr.target_value = input.target_value
        if input.unit is not None:
            kr.unit = input.unit
        kr.updated_at = datetime.now(timezone.utc)
        await self._repo.save_key_result(kr)
        return kr


class DeleteKeyResultUseCase:
    def __init__(self, repository: IGoalRepository) -> None:
        self._repo = repository

    async def execute(self, key_result_id: uuid.UUID) -> None:
        kr = await self._repo.get_key_result(key_result_id)
        if kr is None:
            raise EntityNotFoundError("KeyResult", str(key_result_id))
        await self._repo.delete_key_result(key_result_id)
