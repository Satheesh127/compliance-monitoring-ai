"""LangChain document loading utilities for URL ingestion."""

from __future__ import annotations

import logging
import os
from typing import Iterable, List

# ✅ FIXED IMPORT
from core.config import REQUEST_TIMEOUT, USER_AGENT

os.environ.setdefault("USER_AGENT", USER_AGENT)

from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


def _normalize_urls(urls: Iterable[str]) -> List[str]:
    """Normalize and deduplicate URL inputs while preserving order."""
    seen = set()
    normalized: List[str] = []

    for value in urls:
        url = value.strip()
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        normalized.append(url)

    return normalized


def load_web_documents(urls: Iterable[str]) -> List[Document]:
    """Load documents from one or more web URLs using LangChain WebBaseLoader."""
    normalized_urls = _normalize_urls(urls)
    if not normalized_urls:
        return []

    documents: List[Document] = []

    for url in normalized_urls:
        try:
            loader = WebBaseLoader(
                web_paths=[url],
                requests_kwargs={
                    "timeout": REQUEST_TIMEOUT,
                    "headers": {"User-Agent": USER_AGENT},
                },
            )
            loaded_docs = loader.load()

            for doc in loaded_docs:
                doc.metadata = doc.metadata or {}
                doc.metadata["source"] = doc.metadata.get("source", url)
                doc.metadata["url"] = url

            documents.extend(loaded_docs)
            logger.info("Loaded %s document(s) from %s", len(loaded_docs), url)

        except Exception as exc:
            logger.exception("Failed to load URL %s: %s", url, exc)

    return documents
