from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.ai_advisor import AIAdvisorService
from src.config import settings
from src.domain.cost.repository import ICostRepository
from src.domain.events import IEventBus, InMemoryEventBus
from src.domain.repositories.goal_repository import IGoalRepository
from src.domain.repositories.sprint_repository import ISprintRepository
from src.domain.repositories.task_repository import ITaskRepository
from src.infrastructure.ai.ollama_client import IAIClient, IOllamaClient, OllamaClient
from src.infrastructure.ai.openai_compat_client import OpenAICompatClient
from src.infrastructure.database import get_session
from src.infrastructure.persistence.repositories.cost_repository import PostgresCostRepository
from src.infrastructure.persistence.repositories.goal_repository import PostgresGoalRepository
from src.infrastructure.persistence.repositories.sprint_repository import PostgresSprintRepository
from src.infrastructure.persistence.repositories.task_repository import PostgresTaskRepository

# One event bus for the lifetime of the process
_event_bus = InMemoryEventBus()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_task_repo(session: SessionDep) -> ITaskRepository:
    return PostgresTaskRepository(session)


def get_sprint_repo(session: SessionDep) -> ISprintRepository:
    return PostgresSprintRepository(session)


def get_goal_repo(session: SessionDep) -> IGoalRepository:
    return PostgresGoalRepository(session)


def get_cost_repo(session: SessionDep) -> ICostRepository:
    return PostgresCostRepository(session)


def get_event_bus() -> IEventBus:
    return _event_bus


TaskRepoDep = Annotated[ITaskRepository, Depends(get_task_repo)]
SprintRepoDep = Annotated[ISprintRepository, Depends(get_sprint_repo)]
GoalRepoDep = Annotated[IGoalRepository, Depends(get_goal_repo)]
CostRepoDep = Annotated[ICostRepository, Depends(get_cost_repo)]
EventBusDep = Annotated[IEventBus, Depends(get_event_bus)]

def _build_ai_client() -> IAIClient:
    if settings.ai_provider == "openrouter":
        return OpenAICompatClient(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.ai_api_key,
            model=settings.ai_model,
        )
    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
    )


_ai_client: IAIClient = _build_ai_client()


def get_ai_client() -> IAIClient:
    return _ai_client


# Keep old name for backward compat with any existing references
def get_ollama_client() -> IAIClient:
    return _ai_client


AIClientDep = Annotated[IAIClient, Depends(get_ai_client)]


def get_ai_advisor_service(
    cost_repo: CostRepoDep,
    ai_client: AIClientDep,
) -> AIAdvisorService:
    return AIAdvisorService(cost_repo, ai_client)
