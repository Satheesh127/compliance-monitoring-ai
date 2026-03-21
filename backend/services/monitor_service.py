"""Background regulation monitoring loop for change detection and indexing."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests

from backend.core.config import MONITOR_INTERVAL_SECONDS, REGULATION_SNAPSHOT_PATH, REGULATION_URL
from backend.models.models import ComplianceUpdate
from backend.services.comparison_service import ComparisonService
from backend.services.rag_update_service import UpdateRAGService
from backend.services.update_store import UpdateStore

logger = logging.getLogger(__name__)


class RegulationMonitor:
    """Fetches regulation content periodically and records meaningful changes."""

    def __init__(
        self,
        store: UpdateStore,
        rag_service: UpdateRAGService,
        comparison_service: ComparisonService,
        regulation_url: str = REGULATION_URL,
        interval_seconds: int = MONITOR_INTERVAL_SECONDS,
    ) -> None:
        self.store = store
        self.rag_service = rag_service
        self.comparison_service = comparison_service
        self.regulation_url = regulation_url
        self.interval_seconds = interval_seconds
        self.snapshot_path = Path(REGULATION_SNAPSHOT_PATH)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.previous_content: str | None = self._load_previous_content()

    def _load_previous_content(self) -> str | None:
        if not self.snapshot_path.exists():
            return None
        return self.snapshot_path.read_text(encoding="utf-8")

    def _save_previous_content(self, content: str) -> None:
        self.snapshot_path.write_text(content, encoding="utf-8")

    def _fetch_content(self) -> str:
        response = requests.get(self.regulation_url, timeout=20)
        response.raise_for_status()
        return response.text

    @staticmethod
    def _build_title(summary: str) -> str:
        words = [w for w in summary.replace("\n", " ").split(" ") if w]
        return " ".join(words[:8]).strip().rstrip(".") or "Regulation Update"

    async def run_forever(self) -> None:
        while True:
            try:
                await self.run_once()
            except Exception as exc:
                logger.exception("Monitoring iteration failed: %s", exc)

            await asyncio.sleep(self.interval_seconds)

    async def run_once(self) -> None:
        if not self.regulation_url:
            logger.warning("REGULATION_URL is not configured; skipping monitoring cycle")
            return

        loop = asyncio.get_running_loop()
        new_content = await loop.run_in_executor(None, self._fetch_content)

        if self.previous_content is None:
            self.previous_content = new_content
            self._save_previous_content(new_content)
            logger.info("Initial regulation snapshot saved")
            return

        if new_content.strip() == self.previous_content.strip():
            logger.debug("No regulation change detected")
            return

        comparison = self.comparison_service.compare(self.previous_content, new_content)
        now = datetime.now(tz=timezone.utc)

        update = ComplianceUpdate(
            id=str(uuid.uuid4()),
            title=self._build_title(comparison.summary),
            summary=comparison.summary,
            risk=comparison.risk,
            action=comparison.action,
            timestamp=now,
        )

        self.store.add_update(update)
        self.rag_service.index_update(update)
        self.previous_content = new_content
        self._save_previous_content(new_content)

        logger.info("Regulation change stored: %s (%s)", update.id, update.risk)
