from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class IAIClient(ABC):
    @abstractmethod
    async def is_available(self) -> bool: ...

    @abstractmethod
    async def generate(self, prompt: str, system: str) -> str: ...

    @abstractmethod
    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        yield  # makes this an async generator stub for type-checking purposes


# Keep old name as alias so existing imports don't break
IOllamaClient = IAIClient


class OllamaClient(IAIClient):
    def __init__(self, base_url: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._base_url}/api/tags", timeout=3.0)
                return resp.status_code == 200
        except Exception as exc:
            logger.debug("Ollama not available at %s: %s", self._base_url, exc)
            return False

    async def generate(self, prompt: str, system: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "system": system, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/generate",
                json={"model": self._model, "prompt": prompt, "system": system, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done"):
                        break
