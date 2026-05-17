from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from src.domain.entities import SprintTask, Task
from src.domain.value_objects import TaskStatus


class ITaskRepository(ABC):
    @abstractmethod
    async def get_by_id(self, task_id: uuid.UUID) -> Task | None: ...

    @abstractmethod
    async def save(self, task: Task) -> None: ...

    @abstractmethod
    async def delete(self, task_id: uuid.UUID) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[Task]: ...

    @abstractmethod
    async def list_by_status(self, status: TaskStatus) -> list[Task]: ...

    @abstractmethod
    async def list_by_sprint(
        self,
        sprint_id: uuid.UUID,
        status_filter: TaskStatus | None = None,
    ) -> list[SprintTask]: ...

    @abstractmethod
    async def list_by_sprint_ids(
        self, sprint_ids: list[uuid.UUID]
    ) -> list[SprintTask]: ...

    @abstractmethod
    async def list_by_search(self, query: str) -> list[Task]: ...

    @abstractmethod
    async def list_overdue(self) -> list[Task]: ...
