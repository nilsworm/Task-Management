from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.dependencies import get_ai_advisor_service
from src.api.schemas.ai_schemas import InsightCardResponse
from src.application.services.ai_advisor import AIAdvisorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

AIAdvisorServiceDep = Annotated[AIAdvisorService, Depends(get_ai_advisor_service)]


@router.post("/insights", response_model=list[InsightCardResponse])
async def get_insights(service: AIAdvisorServiceDep) -> list[InsightCardResponse]:
    cards = await service.get_insights()
    return [InsightCardResponse(title=c.title, body=c.body, type=c.type) for c in cards]
