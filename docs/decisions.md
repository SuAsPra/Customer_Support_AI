# Decision Log — Milestone 1

| Date | Decision | Options considered | Chosen | Rationale |
|---|---|---|---|---|
| 2026-11-12 | Backend framework | FastAPI, Flask, Django | FastAPI | Async support, automatic OpenAPI docs, strong Pydantic integration for structured schemas, recommended in spec. |
| 2026-11-12 | Relational database | SQLite, PostgreSQL | SQLite (default), configurable via `DATABASE_URL` | Zero-setup local dev; easy to switch to PostgreSQL for production/team use. |
| 2026-11-12 | Vector database | ChromaDB, FAISS | ChromaDB (persistent) | Simple API, built-in persistence/metadata, sufficient for Milestone 1 scale. |
| 2026-11-12 | Embedding model | OpenAI embeddings, sentence-transformers local | `all-MiniLM-L6-v2` (local default), pluggable | No API key/cost required to run Milestone 1; good baseline quality; config allows switching. |
| 2026-11-12 | Chunk size/overlap | 200-800 tokens variants | ~450 tokens, ~60 overlap (char-approx) | Balance context and precision for support docs; heading-aware splitting to keep sections intact. |
| 2026-11-12 | Top-k retrieval | 3,5,8,10 | 5 (configurable) | Enough context without prompt bloat; adjustable via env/config. |
| 2026-11-12 | PDF extraction | PyPDF, pdfplumber | pypdf | Lightweight, adequate for text-based PDFs in sample KB; can swap if complex layouts appear. |
| 2026-11-12 | LLM for Milestone 1 | Require API key vs optional | Optional (`LLM_PROVIDER=none` supported) | Session config and RAG ingestion/retrieval work without LLM; agents using LLM added in later milestones. |
| 2026-11-12 | Sample domain | E-commerce, telecom, banking, SaaS | E-commerce (ShopNest, fictional) | Clear common scenarios (delivery, returns, billing) and easy to author realistic policies/FAQs. |
| 2026-11-12 | UI in Milestone 1 | Build React/Streamlit now vs API-first | API-first, UI deferred to Milestone 3 | Spec focuses M1 on design, session config, and RAG pipeline; FastAPI docs serve as demo interface. |
| 2026-11-12 | Transcript format (Replay) | Plain text, JSON | JSON list of `{sender,text}` (also accept simple line format) | Unambiguous parsing and extensible; easy to validate. |
