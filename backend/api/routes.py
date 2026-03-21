"""FastAPI routes for compliance updates and chatbot."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.models.models import ComplianceUpdate
from backend.schemas.schemas import ChatRequest, ChatResponse, StatsResponse
from backend.services.registry import ServiceRegistry

router = APIRouter(prefix="/api", tags=["compliance"])


def get_registry() -> ServiceRegistry:
    return ServiceRegistry.get_instance()


@router.get("/updates", response_model=list[ComplianceUpdate])
def get_updates(registry: ServiceRegistry = Depends(get_registry)):
    return registry.store.list_updates()


@router.get("/stats", response_model=StatsResponse)
def get_stats(registry: ServiceRegistry = Depends(get_registry)):
    return registry.store.stats()


@router.post("/chat", response_model=ChatResponse)
def post_chat(payload: ChatRequest, registry: ServiceRegistry = Depends(get_registry)):
    answer = registry.rag_service.ask(payload.question)
    return ChatResponse(response=answer)
