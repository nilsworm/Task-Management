from __future__ import annotations

import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_ai_advisor_service
from src.api.schemas.ai_schemas import AIChatRequest, InsightCardResponse
from src.application.services.ai_advisor import AIAdvisorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

AIAdvisorServiceDep = Annotated[AIAdvisorService, Depends(get_ai_advisor_service)]


@router.post("/insights", response_model=list[InsightCardResponse])
async def get_insights(service: AIAdvisorServiceDep) -> list[InsightCardResponse]:
    cards = await service.get_insights()
    return [InsightCardResponse(title=c.title, body=c.body, type=c.type) for c in cards]


@router.post("/chat")
async def chat(request: AIChatRequest, service: AIAdvisorServiceDep) -> StreamingResponse:
    async def event_generator() -> AsyncIterator[str]:
        async for token in service.stream_chat(request.message):
            safe = token.replace("\n", " ")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
