"""Groq LLM initialization for LangChain chains."""

from __future__ import annotations

import os

from langchain_groq import ChatGroq

from backend.core.config import GROQ_MAX_TOKENS, GROQ_MODEL_NAME, GROQ_TEMPERATURE


def get_groq_llm(
    model_name: str = GROQ_MODEL_NAME,
    temperature: float = GROQ_TEMPERATURE,
    max_tokens: int = GROQ_MAX_TOKENS,
) -> ChatGroq:
    """Create a LangChain ChatGroq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is not set. Add it to your environment or .env file.")

    return ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
    )
