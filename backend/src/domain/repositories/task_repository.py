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
    async def list_by_sprint(self, sprint_id: uuid.UUID) -> list[SprintTask]: ...
