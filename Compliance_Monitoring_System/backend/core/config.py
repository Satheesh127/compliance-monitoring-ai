"""Central configuration for the LangChain-based URL RAG system."""

from pathlib import Path
import os

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"
DATA_DIR = BASE_DIR / "data"
UPDATES_FILE_PATH = DATA_DIR / "updates.json"
REGULATION_SNAPSHOT_PATH = DATA_DIR / "regulation_snapshot.txt"

# Ingestion
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Splitting
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

# Embeddings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Vector store / retrieval
CHROMA_COLLECTION_NAME = "url_rag_langchain"
UPDATES_COLLECTION_NAME = "regulation_updates"
RETRIEVER_K = 10
RETRIEVER_FETCH_K = 24
FALLBACK_RETRIEVER_K = 12
MMR_LAMBDA_MULT = 0.6
RETRIEVER_SCORE_THRESHOLD = 0.2
CHAT_TOP_K = 3

# Strict grounding / fallback
FALLBACK_MESSAGE = "Not found in the document"
MIN_QUERY_DOC_OVERLAP_RATIO = 0.05
MIN_SUPPORT_OVERLAP_RATIO = 0.08
MIN_STATEMENT_SUPPORT_RATIO = 0.45

# LLM (Groq)
GROQ_MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
GROQ_TEMPERATURE = 0.2
GROQ_MAX_TOKENS = 1024

# LLM (OpenAI fallback)
OPENAI_MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = 0.2
OPENAI_MAX_TOKENS = 1024

# Monitoring
REGULATION_URL = os.getenv("REGULATION_URL", "")
MONITOR_INTERVAL_SECONDS = int(os.getenv("MONITOR_INTERVAL_SECONDS", "15"))

# FastAPI / CORS
ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
	if origin.strip()
]

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"