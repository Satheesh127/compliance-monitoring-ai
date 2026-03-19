"""In-memory and JSON persistence for compliance updates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

# ✅ FIXED IMPORT
from models.models import ComplianceUpdate


class UpdateStore:
    """Thread-safe enough store for single-process FastAPI usage."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._updates: List[ComplianceUpdate] = []
        self._load()

    def _load(self) -> None:
        if not self.file_path.exists():
            return

        try:
            raw = json.loads(self.file_path.read_text(encoding="utf-8"))
            self._updates = [ComplianceUpdate(**item) for item in raw]
        except Exception:
            self._updates = []

    def _save(self) -> None:
        payload = [item.model_dump(mode="json") for item in self._updates]
        self.file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_update(self, update: ComplianceUpdate) -> None:
        self._updates.append(update)
        self._save()

    def list_updates(self) -> List[ComplianceUpdate]:
        return sorted(self._updates, key=lambda item: item.timestamp, reverse=True)

    def stats(self) -> dict:
        updates = self.list_updates()
        high_risk_count = sum(1 for item in updates if item.risk.lower() == "high")

        # Regions can be replaced with real metadata extraction later.
        regions = ["US", "EU", "APAC"]

        return {
            "total_updates": len(updates),
            "high_risk_count": high_risk_count,
            "regions": regions,
        }
