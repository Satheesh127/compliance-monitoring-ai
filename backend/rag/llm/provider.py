"""LLM provider utilities for Groq/OpenAI runtime selection."""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backend.core.config import (
    GROQ_MAX_TOKENS,
    GROQ_MODEL_NAME,
    GROQ_TEMPERATURE,
    OPENAI_MAX_TOKENS,
    OPENAI_MODEL_NAME,
    OPENAI_TEMPERATURE,
)
from rag.llm.groq_llm import get_groq_llm


def get_chat_llm() -> BaseChatModel:
    """Return a chat model from Groq when available, else fallback to OpenAI."""
    if os.getenv("GROQ_API_KEY"):
        return get_groq_llm(
            model_name=GROQ_MODEL_NAME,
            temperature=GROQ_TEMPERATURE,
            max_tokens=GROQ_MAX_TOKENS,
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("Set GROQ_API_KEY or OPENAI_API_KEY in your environment.")

    return ChatOpenAI(
        model=OPENAI_MODEL_NAME,
        temperature=OPENAI_TEMPERATURE,
        max_tokens=OPENAI_MAX_TOKENS,
        api_key=openai_api_key,
    )
