"""Simple singleton service registry for FastAPI dependency wiring."""

from __future__ import annotations

import logging
from pathlib import Path

from backend.core.config import UPDATES_FILE_PATH
from backend.services.comparison_service import ComparisonService
from backend.services.monitor_service import RegulationMonitor
from backend.services.rag_update_service import UpdateRAGService
from backend.services.update_store import UpdateStore

logger = logging.getLogger(__name__)


class _UnavailableRAGService:
    """Fallback RAG service used when embeddings/vectorstore init fails."""

    def is_empty(self) -> bool:
        return True

    def index_update(self, update) -> None:  # noqa: D401
        # Keep monitoring flow alive even if vector indexing is temporarily unavailable.
        _ = update

    def ask(self, question: str) -> str:
        _ = question
        return (
            "Summary: Chat service is temporarily unavailable.\n"
            "Risk: Unknown\n"
            "Action:\n"
            "- Check internet/DNS access to huggingface.co\n"
            "- Restart backend after connectivity is restored\n"
            "Source: N/A"
        )


class ServiceRegistry:
    _instance: "ServiceRegistry | None" = None

    def _init_rag(self):
        try:
            return UpdateRAGService()
        except Exception as exc:
            logger.exception("RAG service initialization failed; running in degraded mode: %s", exc)
            return _UnavailableRAGService()

    def __init__(self) -> None:
        self.store = UpdateStore(Path(UPDATES_FILE_PATH))
        self.rag_service = self._init_rag()

        if self.rag_service.is_empty():
            for update in self.store.list_updates():
                self.rag_service.index_update(update)
        self.comparison_service = ComparisonService()
        self.monitor = RegulationMonitor(
            store=self.store,
            rag_service=self.rag_service,
            comparison_service=self.comparison_service,
        )

    @classmethod
    def get_instance(cls) -> "ServiceRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
