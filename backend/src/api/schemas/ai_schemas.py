from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InsightCardResponse(BaseModel):
    title: str
    body: str
    type: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=2000)


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    history: list[ChatMessage] = Field(default_factory=list, max_length=50)
