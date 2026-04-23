from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from src.domain.sprint import Sprint


class ISprintRepository(ABC):
    @abstractmethod
    async def get_by_id(self, sprint_id: uuid.UUID) -> Sprint | None: ...

    @abstractmethod
    async def save(self, sprint: Sprint) -> None: ...

    @abstractmethod
    async def delete(self, sprint_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[Sprint]: ...

    @abstractmethod
    async def get_active(self) -> Sprint | None: ...
