"""RAG chain builders for RetrievalQA and conversational retrieval."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from langchain_classic.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

# ✅ FIXED IMPORTS (removed backend.)
from core.config import (
    FALLBACK_MESSAGE,
    FALLBACK_RETRIEVER_K,
    MIN_QUERY_DOC_OVERLAP_RATIO,
    MIN_SUPPORT_OVERLAP_RATIO,
    RETRIEVER_K,
    RETRIEVER_SCORE_THRESHOLD,
)
from rag.llm.groq_llm import get_groq_llm
from utils.helpers import _query_overlap, _tokenize, _validate_answer_against_context

logger = logging.getLogger(__name__)

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a strict context-only assistant.\n"
        "Rules:\n"
        "1) Use ONLY the provided context.\n"
        "2) Do NOT assume, infer, or add external knowledge.\n"
        "3) Only include facts clearly stated in the context.\n"
        "4) If relevant information is spread across multiple chunks, combine it carefully into one answer.\n"
        "5) Accuracy is more important than completeness.\n"
        "6) Do not guess missing details.\n"
        "7) If uncertain or unsupported, output this exact sentence: Not found in the document\n"
        "8) Keep the answer concise and structured with bullet points when useful.\n"
        "9) For critical facts, quote or closely paraphrase wording from context.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
)

# ✅ REST OF YOUR CODE REMAINS SAME (NO CHANGE)
