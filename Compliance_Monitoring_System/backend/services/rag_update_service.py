"""RAG operations restricted to stored compliance updates."""

from __future__ import annotations

from langchain_classic.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

# ✅ FIXED IMPORTS
from core.config import CHAT_TOP_K, FALLBACK_MESSAGE, UPDATES_COLLECTION_NAME
from models.models import ComplianceUpdate
from rag.llm.provider import get_chat_llm
from rag.retrieval.retriever import build_retriever
from rag.vectorstore.chroma_store import get_vectorstore

UPDATE_CHAT_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a compliance monitoring assistant.\n"
        "Use ONLY the provided context from stored regulation updates.\n"
        "If the answer is not explicitly present, output exactly: Not found in the document\n\n"
        "Return this format exactly:\n"
        "Summary: <short answer>\n"
        "Risk: High|Medium|Low|Unknown\n"
        "Action:\n"
        "- <step 1>\n"
        "- <step 2>\n"
        "Source: <comma separated source ids or timestamps>\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Answer:"
    ),
)


class UpdateRAGService:
    """Indexes updates and serves strict retrieval-augmented answers."""

    def __init__(self) -> None:
        self.vectorstore = get_vectorstore(collection_name=UPDATES_COLLECTION_NAME)
        self.retriever = build_retriever(self.vectorstore, k=CHAT_TOP_K)
        self.chain = self._build_chain()

    def _build_chain(self) -> RetrievalQA:
        return RetrievalQA.from_chain_type(
            llm=get_chat_llm(),
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": UPDATE_CHAT_PROMPT},
        )

    def is_empty(self) -> bool:
        collection = getattr(self.vectorstore, "_collection", None)
        if collection is None:
            return False
        return collection.count() == 0

    def index_update(self, update: ComplianceUpdate) -> None:
        text = (
            f"Summary: {update.summary}\n"
            f"Risk: {update.risk}\n"
            "Action:\n"
            + "\n".join(f"- {item}" for item in update.action)
            + f"\nTimestamp: {update.timestamp.isoformat()}"
        )

        doc = Document(
            page_content=text,
            metadata={
                "source": f"update:{update.id}",
                "update_id": update.id,
                "risk": update.risk,
                "timestamp": update.timestamp.isoformat(),
                "title": update.title,
            },
        )
        self.vectorstore.add_documents([doc])

    def ask(self, question: str) -> str:
        result = self.chain.invoke({"query": question})
        answer = (result.get("result") or "").strip()
        return answer or FALLBACK_MESSAGE
