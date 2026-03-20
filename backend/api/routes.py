"""FastAPI routes for compliance updates and chatbot."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends

# ✅ FIXED IMPORTS (removed backend.)
from models.models import ComplianceUpdate
from schemas.schemas import ChatRequest, ChatResponse, StatsResponse
from services.registry import ServiceRegistry

router = APIRouter(prefix="/api", tags=["compliance"])
logger = logging.getLogger(__name__)


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
    try:
        answer = registry.rag_service.ask(payload.question)
        return ChatResponse(response=answer)
    except Exception as exc:
        logger.exception("Chat request failed: %s", exc)
        return ChatResponse(
            response=(
                "Summary: Unable to process request at the moment.\n"
                "Risk: Unknown\n"
                "Action:\n"
                "- Retry your question in a moment\n"
                "- Verify model/API connectivity\n"
                "Source: N/A"
            )
        )
