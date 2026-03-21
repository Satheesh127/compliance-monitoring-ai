"""RAG chain builders for RetrievalQA and conversational retrieval."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List

from langchain_classic.chains import ConversationalRetrievalChain, RetrievalQA
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

from backend.core.config import (
    FALLBACK_MESSAGE,
    FALLBACK_RETRIEVER_K,
    MIN_STATEMENT_SUPPORT_RATIO,
    MIN_QUERY_DOC_OVERLAP_RATIO,
    MIN_SUPPORT_OVERLAP_RATIO,
    RETRIEVER_K,
    RETRIEVER_SCORE_THRESHOLD,
)
from backend.rag.llm.groq_llm import get_groq_llm

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


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"\b[a-zA-Z0-9]{3,}\b", (text or "").lower())}


def _build_result(
    answer: str,
    docs: List[Any],
    fallback_triggered: bool,
    reason_flags: List[str],
    support_overlap_ratio: float,
) -> Dict[str, Any]:
    sources = [doc.metadata.get("source") or doc.metadata.get("url") or "Unknown" for doc in docs]
    confidence = 0.0 if fallback_triggered else max(0.35, min(0.95, support_overlap_ratio + 0.4))
    return {
        "answer": answer,
        "sources": sources,
        "source_documents": docs,
        "meta": {
            "retrieved_count": len(docs),
            "filtered_count": len(docs),
            "threshold_used": RETRIEVER_SCORE_THRESHOLD,
            "query_doc_overlap_threshold": MIN_QUERY_DOC_OVERLAP_RATIO,
            "fallback_triggered": fallback_triggered,
            "reason_flags": reason_flags,
            "confidence": round(confidence, 2),
            "support_overlap_ratio": round(support_overlap_ratio, 3),
        },
    }


def _split_statements(answer: str) -> List[str]:
    """Split model output into simple factual statements for validation."""
    parts = re.split(r"\n+|(?<=[.!?])\s+", (answer or "").strip())
    return [p.strip(" -\t") for p in parts if p and len(_tokenize(p)) >= 4]


def _statement_supported(statement: str, context_sentences: List[str]) -> bool:
    """Check whether a statement is directly supported by at least one context sentence."""
    st_tokens = _tokenize(statement)
    if not st_tokens:
        return False

    has_negation = any(tok in {"not", "never", "no", "without"} for tok in statement.lower().split())
    best_overlap = 0.0
    negation_aligned = not has_negation

    for sent in context_sentences:
        sent_tokens = _tokenize(sent)
        if not sent_tokens:
            continue
        overlap = len(st_tokens.intersection(sent_tokens)) / len(st_tokens)
        if overlap > best_overlap:
            best_overlap = overlap

        if has_negation and overlap >= MIN_STATEMENT_SUPPORT_RATIO:
            sent_has_negation = any(tok in {"not", "never", "no", "without"} for tok in sent.lower().split())
            negation_aligned = sent_has_negation

    return best_overlap >= MIN_STATEMENT_SUPPORT_RATIO and negation_aligned


def _validate_answer_against_context(answer: str, context_text: str) -> tuple[str, bool]:
    """Remove unsupported statements; return fallback if no grounded content remains."""
    statements = _split_statements(answer)
    if not statements:
        return FALLBACK_MESSAGE, False

    context_sentences = [s.strip() for s in re.split(r"\n+|(?<=[.!?])\s+", context_text) if s.strip()]
    supported = [s for s in statements if _statement_supported(s, context_sentences)]

    if not supported:
        return FALLBACK_MESSAGE, False

    # Preserve structured bullets and avoid over-generation by keeping validated statements only.
    return "\n".join(f"- {s}" for s in supported), len(supported) == len(statements)


def _query_overlap(question: str, text: str) -> float:
    question_tokens = _tokenize(question)
    doc_tokens = _tokenize(text)
    return (len(question_tokens.intersection(doc_tokens)) / len(question_tokens)) if question_tokens else 0.0


def _retrieve_with_threshold(chain: RetrievalQA, question: str) -> List[Any]:
    """Retrieve docs with parent retriever first, then fallback to similarity search."""
    primary_docs = chain.retriever.invoke(question)
    primary_filtered = [
        d for d in primary_docs if _query_overlap(question, d.page_content) >= MIN_QUERY_DOC_OVERLAP_RATIO
    ][:RETRIEVER_K]

    logger.info(
        "Strict RAG retrieval stats: primary_retrieved=%s primary_filtered=%s threshold_used=%.2f",
        len(primary_docs),
        len(primary_filtered),
        RETRIEVER_SCORE_THRESHOLD,
    )
    if primary_filtered:
        logger.info(
            "Primary sources: %s",
            [d.metadata.get("source") or d.metadata.get("url") or "Unknown" for d in primary_filtered[:3]],
        )
        return primary_filtered

    # Fallback retrieval strategy: higher-k similarity search with score logging.
    vectorstore = chain.retriever.vectorstore
    docs_with_scores = vectorstore.similarity_search_with_score(question, k=FALLBACK_RETRIEVER_K)

    filtered: List[Any] = []
    score_trace = []
    for doc, distance in docs_with_scores:
        similarity = 1.0 / (1.0 + max(float(distance), 0.0))
        query_overlap = _query_overlap(question, doc.page_content)
        score_trace.append(round(similarity, 3))
        if similarity >= RETRIEVER_SCORE_THRESHOLD and query_overlap >= MIN_QUERY_DOC_OVERLAP_RATIO:
            filtered.append(doc)
        if len(filtered) >= RETRIEVER_K:
            break

    logger.info(
        "Strict RAG retrieval fallback: retrieved_count=%s filtered_count=%s threshold_used=%.2f scores=%s",
        len(docs_with_scores),
        len(filtered),
        RETRIEVER_SCORE_THRESHOLD,
        score_trace,
    )
    return filtered


def build_retrieval_qa_chain(retriever) -> RetrievalQA:
    """Build a classic RetrievalQA chain with chain_type='stuff'."""
    llm = get_groq_llm()
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )


def build_conversational_chain(retriever) -> ConversationalRetrievalChain:
    """Optional conversational chain with buffer memory."""
    llm = get_groq_llm()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )

    return ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=True,
    )


def run_retrieval_qa(chain: RetrievalQA, question: str) -> Dict[str, Any]:
    """Run strict RetrievalQA with pre/post grounding guardrails and metadata."""
    reason_flags: List[str] = []

    # Pre-check: If no documents pass threshold retrieval, skip LLM call.
    docs = _retrieve_with_threshold(chain, question)
    retrieved_count = len(docs)
    if retrieved_count == 0:
        reason_flags.append("no_retrieved_context")
        logger.info(
            "Strict RAG decision: retrieved_count=%s filtered_count=%s threshold_used=%.2f fallback_triggered=%s",
            retrieved_count,
            0,
            RETRIEVER_SCORE_THRESHOLD,
            True,
        )
        return _build_result(
            answer=FALLBACK_MESSAGE,
            docs=[],
            fallback_triggered=True,
            reason_flags=reason_flags,
            support_overlap_ratio=0.0,
        )

    # Call the chain only when threshold-relevant docs exist.
    result = chain.invoke({"query": question})
    answer = (result.get("result") or "").strip()
    source_docs = result.get("source_documents") or docs

    if not source_docs:
        reason_flags.append("empty_sources")
        logger.info(
            "Strict RAG decision: retrieved_count=%s filtered_count=%s threshold_used=%.2f fallback_triggered=%s",
            retrieved_count,
            0,
            RETRIEVER_SCORE_THRESHOLD,
            True,
        )
        return _build_result(
            answer=FALLBACK_MESSAGE,
            docs=[],
            fallback_triggered=True,
            reason_flags=reason_flags,
            support_overlap_ratio=0.0,
        )

    context_text = " ".join(doc.page_content for doc in source_docs)
    validated_answer, fully_supported = _validate_answer_against_context(answer, context_text)
    if validated_answer != answer:
        reason_flags.append("unsupported_claims_removed")
    answer = validated_answer

    answer_tokens = _tokenize(answer)
    context_tokens = _tokenize(context_text)
    overlap = answer_tokens.intersection(context_tokens)
    support_overlap_ratio = (len(overlap) / len(answer_tokens)) if answer_tokens else 0.0

    fallback_triggered = False
    if support_overlap_ratio < MIN_SUPPORT_OVERLAP_RATIO or not fully_supported:
        reason_flags.append("low_context_support")
        answer = FALLBACK_MESSAGE
        fallback_triggered = True

    logger.info(
        "Strict RAG decision: retrieved_count=%s filtered_count=%s threshold_used=%.2f fallback_triggered=%s",
        retrieved_count,
        len(source_docs),
        RETRIEVER_SCORE_THRESHOLD,
        fallback_triggered,
    )
    return _build_result(
        answer=answer,
        docs=source_docs,
        fallback_triggered=fallback_triggered,
        reason_flags=reason_flags,
        support_overlap_ratio=support_overlap_ratio,
    )


def run_conversational_qa(chain: ConversationalRetrievalChain, question: str) -> Dict[str, Any]:
    """Run conversational retrieval with strict no-context fallback behavior."""
    docs = _retrieve_with_threshold(chain, question)
    retrieved_count = len(docs)
    if retrieved_count == 0:
        logger.info(
            "Strict RAG decision: retrieved_count=%s filtered_count=%s threshold_used=%.2f fallback_triggered=%s",
            retrieved_count,
            0,
            RETRIEVER_SCORE_THRESHOLD,
            True,
        )
        return _build_result(
            answer=FALLBACK_MESSAGE,
            docs=[],
            fallback_triggered=True,
            reason_flags=["no_retrieved_context"],
            support_overlap_ratio=0.0,
        )

    result = chain.invoke({"question": question})
    answer = (result.get("answer") or "").strip()
    source_docs = result.get("source_documents") or docs
    if not answer:
        return _build_result(
            answer=FALLBACK_MESSAGE,
            docs=source_docs,
            fallback_triggered=True,
            reason_flags=["empty_answer"],
            support_overlap_ratio=0.0,
        )
    context_text = " ".join(doc.page_content for doc in source_docs)
    validated_answer, fully_supported = _validate_answer_against_context(answer, context_text)
    reason_flags: List[str] = []
    if validated_answer != answer:
        reason_flags.append("unsupported_claims_removed")
    answer = validated_answer
    if not fully_supported:
        reason_flags.append("low_context_support")
        answer = FALLBACK_MESSAGE

    logger.info(
        "Strict RAG decision: retrieved_count=%s filtered_count=%s threshold_used=%.2f fallback_triggered=%s",
        retrieved_count,
        len(source_docs),
        RETRIEVER_SCORE_THRESHOLD,
        answer == FALLBACK_MESSAGE,
    )
    return _build_result(
        answer=answer or FALLBACK_MESSAGE,
        docs=source_docs,
        fallback_triggered=(answer == FALLBACK_MESSAGE),
        reason_flags=reason_flags if answer else ["empty_answer"],
        support_overlap_ratio=0.2 if answer and answer != FALLBACK_MESSAGE else 0.0,
    )
