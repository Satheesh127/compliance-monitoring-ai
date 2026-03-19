"""LLM-based semantic comparison between previous and latest regulation text."""

from __future__ import annotations

import re
from typing import List

from langchain_core.prompts import PromptTemplate

# ✅ FIXED IMPORTS
from models.models import ComparisonResult
from rag.llm.provider import get_chat_llm

COMPARE_PROMPT = PromptTemplate(
    input_variables=["old_content", "new_content"],
    template=(
        "You compare two versions of a regulation document and extract meaningful policy changes.\n"
        "Be concise and strict.\n"
        "Output exactly this format:\n"
        "Summary: <max 120 words>\n"
        "Risk: High|Medium|Low\n"
        "Action:\n"
        "- <first action>\n"
        "- <second action>\n\n"
        "OLD:\n{old_content}\n\n"
        "NEW:\n{new_content}\n"
    ),
)


def _extract_field(pattern: str, content: str, default: str = "") -> str:
    match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return default
    return match.group(1).strip()


def _extract_actions(content: str) -> List[str]:
    action_block = _extract_field(r"Action:\s*(.*)$", content, "")
    if not action_block:
        return []

    actions: List[str] = []
    for line in action_block.splitlines():
        cleaned = line.strip().lstrip("-*").strip()
        if cleaned:
            actions.append(cleaned)
    return actions


def _normalize_risk(value: str) -> str:
    normalized = value.strip().capitalize()
    if normalized not in {"High", "Medium", "Low"}:
        return "Medium"
    return normalized


class ComparisonService:
    """Compares two document versions using an LLM semantic judgment."""

    def __init__(self) -> None:
        self.llm = get_chat_llm()

    def compare(self, old_content: str, new_content: str) -> ComparisonResult:
        response = self.llm.invoke(
            COMPARE_PROMPT.format(
                old_content=old_content[:10000],
                new_content=new_content[:10000]
            )
        )
        text = response.content if isinstance(response.content, str) else str(response.content)

        summary = _extract_field(
            r"Summary:\s*(.*?)\nRisk:",
            text,
            "Regulation updated with notable changes."
        )
        risk = _normalize_risk(_extract_field(r"Risk:\s*(.*?)\n", text, "Medium"))
        actions = _extract_actions(text) or [
            "Review updated regulation text",
            "Update internal controls"
        ]

        return ComparisonResult(summary=summary, risk=risk, action=actions)
