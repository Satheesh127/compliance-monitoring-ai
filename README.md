# AI Compliance Monitoring System

Extended LangChain-based RAG platform with real-time regulation change monitoring.

## What Was Added

- FastAPI backend for updates, stats, and chatbot APIs
- Async background monitor that checks `REGULATION_URL` every 15 seconds
- LLM-based semantic comparison for change detection (`Summary`, `Risk`, `Action`)
- Persistent update storage in JSON and memory
- Update indexing into ChromaDB for strict update-only RAG chatbot responses
- React (Vite) + Tailwind frontend with only two pages:
  - Dashboard
  - Chatbot

Your existing URL ingestion/splitting/retrieval/RAG modules remain intact and reusable.

## Backend Structure

```text
backend/
  fastapi_app.py
  api/
    routes.py
  schemas/
    schemas.py
  models/
    models.py
  services/
    comparison_service.py
    monitor_service.py
    rag_update_service.py
    registry.py
    update_store.py
  rag/
    ingestion/loader.py
    processing/splitter.py
    retrieval/retriever.py
    chains/rag_chain.py
    llm/groq_llm.py
    llm/provider.py
    vectorstore/chroma_store.py
  core/
    config.py
  utils/
    helpers.py
```

## Frontend Structure

```text
frontend/
  src/
    api/client.js
    components/
      Navbar.jsx
      UpdateCard.jsx
      UpdateModal.jsx
      ChatMessage.jsx
    pages/
      DashboardPage.jsx
      ChatbotPage.jsx
    App.jsx
    main.jsx
    index.css
```

## Environment Variables

Create/update `.env` in project root:

```env
# Monitoring
REGULATION_URL=https://example.com/regulation-page
MONITOR_INTERVAL_SECONDS=15

# LLM (Groq preferred)
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant

# Optional OpenAI fallback
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o-mini

# CORS
ALLOWED_ORIGINS=http://localhost:5173
```

Runtime note:
- The backend currently reads these env vars at startup: `REGULATION_URL`, `MONITOR_INTERVAL_SECONDS`, `GROQ_API_KEY`, `GROQ_MODEL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `ALLOWED_ORIGINS`.
- Temperature/max token values are currently defined in `backend/core/config.py`.

## Install

Backend:

```bash
pip install -r requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

## Run

Backend (FastAPI):

```bash
uvicorn backend.fastapi_app:app --reload --port 8000
```

Frontend (Vite):

```bash
cd frontend
npm run dev
```

## Deployment Mode Policy

- Embedded monitor mode (current default): run a single API worker so only one monitor loop runs.
  ```bash
  uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000 --workers 1
  ```
- If you need multiple API workers, move monitoring to a separate dedicated process/service and disable it in API workers.

## API Endpoints

- `GET /api/updates`
  - Returns all updates (latest first)
- `GET /api/stats`
  - Returns `total_updates`, `high_risk_count`, `regions`
- `POST /api/chat`
  - Request:
    ```json
    { "question": "What changed in the latest update?" }
    ```
  - Response:
    ```json
    { "response": "Summary: ...\nRisk: ...\nAction: ...\nSource: ..." }
    ```

## Monitoring Flow

1. Background loop starts on FastAPI startup.
2. Every 15 seconds, fetches `REGULATION_URL` content.
3. First run stores snapshot and skips compare.
4. On content change (`strip()` comparison), calls LLM semantic comparator.
5. Stores structured update with fields:
   - `id` (uuid)
   - `title`
   - `summary`
   - `risk`
   - `action` (list)
   - `timestamp`
6. Saves update to JSON and ChromaDB.
7. Chatbot retrieves only from stored updates (`top_k=3`).
