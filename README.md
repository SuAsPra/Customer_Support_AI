# AI Customer Support Coaching Assistant

An AI platform that coaches support agents during live text-based conversations. A pipeline of AI agents analyzes customer intent and mood, retrieves relevant knowledge (RAG), suggests responses, evaluates tone/clarity, monitors escalation risk, and produces post-interaction coaching reports. The console is designed as three panels: conversation, real-time coaching feed, and knowledge recommendations.

**Current status:** Milestone 1 implemented (design, research, session configuration module, KB ingestion & RAG pipeline, sample KB + retrieval test set). Milestones 2–4 are scaffolded in data models and design.

## Project Overview and Features

### Core vision
- **Multi-agent real-time coaching pipeline** per conversation turn
- **Three interaction modes** (same pipeline, different message source): Simulator, Manual, Replay
- **RAG-powered knowledge recommendations** from uploaded FAQs/policies/docs
- **Escalation risk detection** with reasoning and recommended actions
- **Post-interaction reports** with sentiment journey, resolution quality score, and personalized coaching

### Milestone 1 features (implemented)
- **Session Configuration module**: create sessions in `simulator`/`manual`/`replay` modes with product context, customer scenario, persona & emotional progression (simulator), and transcript ingestion (replay). Persisted and retrievable via API.
- **Knowledge Base ingestion & RAG**: upload PDF/TXT/MD, extract text, heading-aware chunking, embeddings, ChromaDB indexing, and retrieval returning ranked chunks with source/section/score.
- **Sample domain**: fictional **ShopNest** e-commerce KB and 5 scenarios.
- **Retrieval test set**: 15 questions with expected document/section + evaluation script and results doc.
- **Technical documentation**: architecture, 6-agent specs, orchestration, data models/ER diagram, API outline, agent output schemas, research summaries, decision log.

## Technology Stack

| Area | Choice (Milestone 1) | Notes |
|---|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn | Async API, OpenAPI docs, Pydantic schemas |
| Relational DB | SQLite (SQLAlchemy) | Default local; configurable to PostgreSQL via `DATABASE_URL` |
| Vector DB | ChromaDB (persistent) | Local persistent store for embeddings/metadata |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (default) | Local, no API cost; pluggable via config |
| PDF extraction | pypdf | Text extraction for PDFs |
| LLM (M2+) | OpenAI / Gemini / Anthropic / Ollama | Configurable; not required for M1 RAG/session config |
| Frontend (M3) | React or Streamlit (TBD) | Placeholder in `frontend/` for Milestone 3 |
| Tools | Git, pytest, Swagger/Postman | |

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/             # sessions, kb, health routes
│   │   ├── core/            # configuration
│   │   ├── db/              # SQLAlchemy engine/models
│   │   ├── models/          # Pydantic schemas
│   │   ├── rag/             # extract, chunk, vectorstore
│   │   ├── services/        # session_service, kb_service
│   │   └── main.py          # FastAPI app
│   ├── scripts/
│   │   └── evaluate_retrieval.py
│   └── requirements.txt
├── docs/
│   ├── design_document.md   # architecture, agents, orchestration, ERD, API, schemas
│   ├── decisions.md         # decision log
│   ├── retrieval_test_results.md
│   └── research/            # 5 study summaries
├── sample_kb/
│   ├── shopnest/            # FAQ, refund_policy, shipping_and_delivery, troubleshooting
│   ├── retrieval_test_set.json
│   └── scenarios.md
├── frontend/                # placeholder (Milestone 3)
├── .env.example
├── .gitignore
└── README.md
```

## Prerequisites

- **Python** 3.11+ (recommended)
- **Git**
- **pip** and virtual environment support
- **Internet access** on first run to download the local embedding model (`sentence-transformers/all-MiniLM-L6-v2`) unless cached
- (Optional, Milestone 2+) LLM API key (OpenAI/Gemini/Anthropic) or local Ollama

## Installation Steps

1. **Open project root**
   ```powershell
   cd C:\Customer_Service_AI
   ```
2. **Create and activate a virtual environment**
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
3. **Install backend dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Create environment file**
   ```powershell
   copy .env.example .env
   ```
   Edit `.env` as needed (see below). Defaults are sufficient for Milestone 1.

## Environment Variable Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Environment name |
| `APP_HOST` / `APP_PORT` | `0.0.0.0` / `8000` | Backend bind host/port |
| `DATABASE_URL` | `sqlite:///./data/app.db` | Relational DB connection (SQLite by default) |
| `LLM_PROVIDER` | `none` | `openai`/`gemini`/`anthropic`/`ollama`/`none` (M2+) |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` / `ANTHROPIC_API_KEY` | empty | LLM credentials (M2+) |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | local defaults | Local Ollama config (M2+) |
| `EMBEDDING_PROVIDER` | `sentence-transformers` | Embedding backend |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Vector store persistence path |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `450` / `60` | Token-target chunking params (approx) |
| `RETRIEVAL_TOP_K` | `5` | Default number of retrieved chunks |
| `UPLOAD_DIR` | `./data/uploads` | Uploaded KB file storage |

> **Security:** Never commit `.env` or API keys. `.gitignore` excludes `.env`, `data/`, vector stores, and uploads.

## Database Setup

- **Relational DB (default):** SQLite at `./data/app.db` (auto-created on first run). Tables are created automatically at app startup (`Base.metadata.create_all`). No manual migration step required for Milestone 1.
- **PostgreSQL (optional):** set `DATABASE_URL` (e.g. `postgresql+psycopg://user:pass@host:5432/dbname`) and install an appropriate driver (e.g. `psycopg[binary]`) if needed.
- **Vector DB:** ChromaDB persists to `CHROMA_PERSIST_DIR` (default `./data/chroma`) automatically during indexing.

## Backend Execution Steps

From the repository root with the virtual environment activated:

```bash
uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
```

- API base: `http://localhost:8000`
- Swagger UI (interactive API docs): `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- Health check: `GET http://localhost:8000/api/health`

## Frontend Execution Steps (Milestone 3 placeholder)

- The `frontend/` directory is a **placeholder** for Milestone 3 (Live Support Console UI).
- No frontend build/run is required for Milestone 1; use **Swagger UI** (`/docs`), **Postman**, or curl to demonstrate session creation, KB upload, and retrieval.
- When Milestone 3 begins, this section will be updated with the chosen stack (React or Streamlit), install, and run commands.

## RAG Pipeline Setup

1. Start the backend (see above).
2. **Upload documents** via `POST /api/kb/documents` (multipart form field: `file`) with `.pdf`, `.txt`, or `.md` files (sample: `sample_kb/shopnest/*.md`).
   - Pipeline stages on upload: **save → extract text → chunk → embed → index in ChromaDB** (metadata stored in relational DB).
3. **Verify indexing** via `GET /api/kb/documents` (status `indexed`, `chunk_count`, errors if any).
4. **Retrieve** via `POST /api/kb/retrieve` with `{"query": "...", "top_k": 5}` to get ranked chunks with `source`, `section`, `score`, and text.
5. **Reindex** a document if needed: `POST /api/kb/documents/{doc_id}/reindex`.
6. **Evaluate** against the 15-question test set:
   ```bash
   python backend/scripts/evaluate_retrieval.py
   ```
   Updates `docs/retrieval_test_results.md` with summary and per-question actual results.

**RAG design choices (documented):** chunk ~450 tokens, overlap ~60, heading-aware splitting, `all-MiniLM-L6-v2` embeddings, ChromaDB cosine space, top-k 5. See `docs/design_document.md` and `docs/decisions.md`.

## API Documentation References

- **Interactive (source of truth):** Swagger UI at `/docs`, ReDoc at `/redoc` (when backend is running)
- **Design/API outline:** `docs/design_document.md` (Section 5: endpoints, request/response fields, sample structures)
- **Agent output schemas:** `docs/design_document.md` (Section 6: sample JSON for all 6 agents)

### Key Milestone 1 endpoints
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health/status |
| POST | `/api/sessions` | Create session (simulator/manual/replay) |
| GET | `/api/sessions` | List sessions |
| GET | `/api/sessions/{id}` | Get session |
| POST | `/api/kb/documents` | Upload & index KB document |
| GET | `/api/kb/documents` | List KB documents |
| POST | `/api/kb/documents/{id}/reindex` | Reindex document |
| POST | `/api/kb/retrieve` | Retrieve relevant chunks |

**Example: create session (Simulator)**
```json
POST /api/sessions
{
  "mode": "simulator",
  "product_context": "ShopNest e-commerce support",
  "scenario": "Customer charged twice for subscription",
  "persona": "impatient",
  "emotional_progression": "frustrated -> angry if unresolved -> relieved if refund confirmed"
}
```
**Example: retrieve**
```json
POST /api/kb/retrieve
{ "query": "I was charged twice for my subscription. What should I do?", "top_k": 5 }
```

## Milestone 1 Demonstration Guide

During review, demonstrate:
1. **Session creation in all three modes** via `/docs`: Simulator (with persona/progression), Manual, Replay (with transcript). Show stored config via `GET /api/sessions/{id}` (and stored replay messages in DB behavior as implemented).
2. **Product context & customer scenario configuration**: fields accepted/persisted in created session.
3. **Upload support documents**: upload `sample_kb/shopnest/*.md` (and/or a PDF) via `POST /api/kb/documents`.
4. **Document processing, chunking, vector indexing**: show `status=indexed` and `chunk_count` in `GET /api/kb/documents`.
5. **Retrieve relevant information**: run sample questions from `sample_kb/retrieval_test_set.json` via `POST /api/kb/retrieve`.
6. **Display retrieved content and source**: show returned `text`, `source`, `section`, and `score` for results.

Supporting artifacts: `docs/design_document.md`, `docs/research/*`, `docs/retrieval_test_results.md`, `sample_kb/*`.

## Troubleshooting

| Issue | Possible cause | Fix |
|---|---|---|
| `ModuleNotFoundError: app` when starting | Run from wrong directory or missing `--app-dir` | Run from repo root: `uvicorn app.main:app --app-dir backend ...` |
| First upload/index is slow or hangs | Downloading embedding model | Wait for `all-MiniLM-L6-v2` download; ensure internet on first run |
| `sentence-transformers`/torch install issues on Windows | Heavy deps/build issues | Use Python 3.11, upgrade pip (`python -m pip install -U pip`), install CPU wheels; retry install |
| PDF upload returns "No extractable text" or fails | Scanned/image PDF or complex layout | Use text-based PDFs or `.md/.txt`; OCR not included in M1 |
| Retrieval returns empty results | No documents indexed or query mismatch | Check `GET /api/kb/documents` for `indexed` status and `chunk_count > 0`; reindex if needed |
| `Unsupported file type` | Extension not allowed | Only `.pdf`, `.txt`, `.md` supported |
| Chroma/SQLite permission or path errors | `data/` path not writable | Ensure repo directory is writable; adjust `CHROMA_PERSIST_DIR`, `DATABASE_URL`, `UPLOAD_DIR` in `.env` |
| Port 8000 in use | Another service running | Change `--port` or `APP_PORT` and update URLs |
| Replay session validation error | Missing transcript | Provide `transcript` (JSON list or `sender: text` lines) for `mode=replay` |
| Simulator session validation error | Missing persona | Provide `persona` for `mode=simulator` |

## Milestone 1 Checklist (per submission guidelines)

- [x] **Design document**: architecture, 6 agent specs/responsibilities, orchestration flow, DB design/data models/ER diagram, API outline with request/response structures, agent output schemas with sample JSON
- [x] **Research summaries**: 5 topics (definitions, terminologies, explanations, examples, application to project)
- [x] **Session Configuration module**: Simulator/Manual/Replay, product context, scenario, session creation, backend integration
- [x] **KB ingestion & RAG pipeline**: upload, extract, chunk, embeddings, vector storage, retrieval
- [x] **Sample KB & retrieval test set**: sample docs, 15 questions with expected info/source, evaluation script + results documentation
- [x] **Demonstration readiness**: steps cover all required demo points
- [x] **README/setup docs**: overview/features, tech stack, prerequisites/install, env vars, DB setup, backend/frontend steps, RAG setup, API refs, troubleshooting

## Requirements / Inputs Needed from You (please provide)

To validate in your environment and proceed to Milestones 2–4, please share:

1. **LLM provider & API key (for Milestone 2+ agents)**: OpenAI (`OPENAI_API_KEY`, model), Gemini (`GEMINI_API_KEY`), Anthropic (`ANTHROPIC_API_KEY`), or local Ollama (`OLLAMA_BASE_URL`, model) — and any budget/rate limits.
2. **OpenCode or platform-specific API key/token** (if applicable): if this project must use a specific "OpenCode API" key or other environment credential, paste the key or tell me the exact env var name so I can wire it into `.env`/config.
3. **Database URL** (optional): keep default SQLite or provide PostgreSQL/shared DB connection string.
4. **Embeddings preference** (optional): keep local `sentence-transformers` or use provider embeddings (share provider/key/model).
5. **Frontend choice for Milestone 3**: React or Streamlit.
6. **Product domain confirmation**: keep fictional **ShopNest** or switch to another domain for samples.
7. **Confirmation to proceed**: once you provide the above, should I implement **Milestone 2** (Customer Simulator, Intent & Sentiment, Knowledge Recommendation agents + orchestration/testing)?

> Paste any secrets here only if appropriate for this environment; I will store them in `.env` (gitignored), not in committed files.

## License / Data
Sample knowledge base and scenarios are fictional and for educational use only. No real or confidential customer data.
