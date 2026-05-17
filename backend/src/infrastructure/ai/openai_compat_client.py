from __future__ import annotations

import logging
from typing import AsyncIterator

from openai import AsyncOpenAI

from src.infrastructure.ai.ollama_client import IAIClient

logger = logging.getLogger(__name__)


class OpenAICompatClient(IAIClient):
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._model = model
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            default_headers={"X-Title": "Task Manager AI Advisor"},
        )

    async def is_available(self) -> bool:
        return True

    async def generate(self, prompt: str, system: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return response.choices[0].message.content or ""

    async def generate_stream(self, prompt: str, system: str) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content
