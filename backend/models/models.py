"""Shared data models for compliance monitoring updates."""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class ComplianceUpdate(BaseModel):
    """Canonical update record returned by API and stored on disk."""

    id: str
    title: str
    summary: str
    risk: str
    action: List[str] = Field(default_factory=list)
    timestamp: datetime


class ComparisonResult(BaseModel):
    """Structured LLM output for regulation changes."""

    summary: str
    risk: str
    action: List[str] = Field(default_factory=list)
