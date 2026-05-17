from __future__ import annotations

from pydantic import BaseModel, Field


class InsightCardResponse(BaseModel):
    title: str
    body: str
    type: str


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
