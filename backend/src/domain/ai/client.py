from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class IAIClient(ABC):
    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    async def generate(self, prompt: str, system: str) -> str: ...

    @abstractmethod
    async def generate_stream(
        self, messages: list[dict[str, str]], system: str
    ) -> AsyncIterator[str]:
        yield  # makes this an async generator stub for type-checking purposes
