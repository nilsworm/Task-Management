from __future__ import annotations

import logging
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
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
    stream = service.stream_chat(request.message)

    # Prime the stream to catch availability errors before committing to a 200 response.
    try:
        first_token = await stream.__anext__()
    except StopAsyncIteration:
        first_token = None
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="AI service unavailable") from exc

    async def event_generator() -> AsyncIterator[str]:
        if first_token is not None:
            safe = first_token.replace("\n", " ")
            yield f"data: {safe}\n\n"
        async for token in stream:
            safe = token.replace("\n", " ")
            yield f"data: {safe}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
