from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from src.domain.entities import LongTermGoal


class IGoalRepository(ABC):
    @abstractmethod
    async def get_by_id(self, goal_id: uuid.UUID) -> LongTermGoal | None: ...

    @abstractmethod
    async def save(self, goal: LongTermGoal) -> None: ...

    @abstractmethod
    async def delete(self, goal_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[LongTermGoal]: ...
