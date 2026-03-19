"""Retriever builders for LangChain vector stores."""

from __future__ import annotations

from backend.core.config import MMR_LAMBDA_MULT, RETRIEVER_FETCH_K, RETRIEVER_K


def build_retriever(
    vectorstore,
    k: int = RETRIEVER_K,
):
    """Create an MMR retriever to balance relevance and chunk diversity."""
    return vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": k,
            "fetch_k": RETRIEVER_FETCH_K,
            "lambda_mult": MMR_LAMBDA_MULT,
        },
    )
