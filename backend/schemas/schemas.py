"""Pydantic schemas for API payloads."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    response: str


class StatsResponse(BaseModel):
    total_updates: int
    high_risk_count: int
    regions: List[str]
