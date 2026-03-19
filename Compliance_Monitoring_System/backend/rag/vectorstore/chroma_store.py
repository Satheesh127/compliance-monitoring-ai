"""Chroma vector store setup and indexing via LangChain."""

from __future__ import annotations

import logging
import shutil
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings  # ✅ lightweight

# ✅ FIXED IMPORT
from core.config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)


# ✅ Lightweight embeddings (no torch / transformers)
@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings()


def get_vectorstore(
    persist_directory: Optional[Path] = None,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> Chroma:
    """Get an existing Chroma vector store handle."""
    persist_path = Path(persist_directory or CHROMA_PERSIST_DIR)
    persist_path.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_path),
        embedding_function=get_embeddings(),
    )


def index_documents(
    documents: List[Document],
    persist_directory: Optional[Path] = None,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> Chroma:
    """Index documents into Chroma and return the vector store instance."""
    if not documents:
        raise ValueError("No documents provided for indexing.")

    vectorstore = get_vectorstore(
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    vectorstore.add_documents(documents)

    if hasattr(vectorstore, "persist"):
        vectorstore.persist()

    logger.info("Indexed %s chunks into Chroma collection '%s'", len(documents), collection_name)
    return vectorstore


def reset_vectorstore(persist_directory: Optional[Path] = None) -> None:
    """Delete the persisted Chroma directory for a clean re-index."""
    persist_path = Path(persist_directory or CHROMA_PERSIST_DIR)
    if persist_path.exists():
        shutil.rmtree(persist_path)
        logger.info("Removed existing Chroma store at %s", persist_path)
    persist_path.mkdir(parents=True, exist_ok=True)
