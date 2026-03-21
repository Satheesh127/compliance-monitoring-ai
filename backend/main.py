"""CLI entrypoint for LangChain-native URL RAG."""

from __future__ import annotations

import argparse
import logging
from typing import List

from dotenv import load_dotenv

from backend.core.config import LOG_FORMAT, LOG_LEVEL
from backend.rag.ingestion.loader import load_web_documents
from backend.rag.processing.splitter import split_documents
from backend.rag.vectorstore.chroma_store import index_documents, get_vectorstore
from backend.rag.retrieval.retriever import build_retriever
from backend.rag.chains.rag_chain import build_retrieval_qa_chain, run_retrieval_qa

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)


def _interactive_urls() -> List[str]:
    """Collect URL input from terminal."""
    print("Enter documentation URLs (one per line). Submit an empty line to continue.")
    urls: List[str] = []
    while True:
        value = input("URL: ").strip()
        if not value:
            break
        urls.append(value)
    return urls


def _interactive_qa() -> None:
    """Run terminal Q&A loop using RetrievalQA."""
    vectorstore = get_vectorstore()
    retriever = build_retriever(vectorstore)
    qa_chain = build_retrieval_qa_chain(retriever)

    print("\nRAG ready. Ask questions (`quit` to exit).")
    while True:
        question = input("\nQuestion: ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit", "q"}:
            break

        answer, sources = run_retrieval_qa(qa_chain, question)
        print(f"\nAnswer:\n{answer}\n")
        if sources:
            print("Sources:")
            for idx, src in enumerate(sources, start=1):
                print(f"  {idx}. {src}")


def main() -> None:
    """Index URLs then run RetrievalQA."""
    load_dotenv()

    parser = argparse.ArgumentParser(description="LangChain URL RAG CLI")
    parser.add_argument("--urls", nargs="*", help="One or more URLs to ingest")
    parser.add_argument("--question", help="Ask one question and exit")
    args = parser.parse_args()

    urls = args.urls or _interactive_urls()
    if not urls:
        print("No URLs provided. Exiting.")
        return

    logger.info("Loading web documents")
    docs = load_web_documents(urls)
    if not docs:
        print("No content loaded from the provided URLs.")
        return

    logger.info("Splitting documents")
    split_docs = split_documents(docs)

    logger.info("Indexing chunks into Chroma")
    index_documents(split_docs)

    vectorstore = get_vectorstore()
    retriever = build_retriever(vectorstore)
    qa_chain = build_retrieval_qa_chain(retriever)

    if args.question:
        answer, sources = run_retrieval_qa(qa_chain, args.question)
        print(f"\nAnswer:\n{answer}\n")
        if sources:
            print("Sources:")
            for idx, src in enumerate(sources, start=1):
                print(f"  {idx}. {src}")
        return

    _interactive_qa()


if __name__ == "__main__":
    main()
