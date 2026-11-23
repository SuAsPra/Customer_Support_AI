# Research Summary: RAG Architecture

## Definitions
- **RAG (Retrieval-Augmented Generation)**: a pattern that retrieves relevant external information (documents/chunks) at query time and provides it as context to an LLM to generate grounded responses.
- **Grounding**: basing model outputs on retrieved source content to improve factuality and relevance.
- **Knowledge base (KB)**: the collection of documents (FAQs, policies, guides) used as the retrieval source.

## Important Terminologies
- **Document loading/ingestion**: importing files and extracting text and metadata.
- **Chunking**: splitting documents into smaller units for indexing/retrieval.
- **Overlap**: shared text between adjacent chunks to preserve context across boundaries.
- **Embedding**: a numeric vector representing semantic meaning of text.
- **Vector database/index**: storage optimized for similarity search over embeddings (e.g. ChromaDB, FAISS).
- **Similarity search**: finding vectors closest to a query vector (cosine similarity, dot product, L2 distance).
- **Top-k retrieval**: returning the k most similar results.
- **Metadata**: attributes like source filename, section/heading, page, chunk index used for filtering and attribution.
- **Reranking/hybrid search**: techniques to improve retrieval quality (combining keyword + vector, rescoring results).

## Explanations
### Pipeline stages
1. **Document loading**: ingest PDFs/text/markdown, extract text, preserve metadata (source, page/section).
2. **Chunking**: split into manageable pieces (fixed/recursive/semantic). Choose chunk size and overlap to balance specificity and context; keep headings with content when possible.
3. **Embeddings**: convert chunks and queries into vectors using the same embedding model for consistency.
4. **Vector storage/indexing**: store vectors with IDs and metadata in a vector DB for efficient nearest-neighbor search.
5. **Similarity search (retrieval)**: embed query, retrieve top-k chunks and scores; optionally filter by metadata.
6. **Augmented generation**: pass retrieved chunks (with sources) into an LLM prompt with instructions to answer based on context.

### Common failure modes
- **Poor chunking**: context split or noisy chunks reduce relevance.
- **Embedding mismatch/domain gap**: wrong or inconsistent models weaken similarity.
- **Retrieval misses**: correct chunk not in top-k (query phrasing, k too small).
- **Context overload/irrelevance**: too many/low-quality chunks confuse the model.
- **Extraction errors**: bad PDF parsing yields unusable text.
- **Stale/missing KB**: required knowledge not ingested.
- **Hallucination despite context**: model ignores/misuses provided evidence without strong prompting/validation.

## Real-World Examples
- **Policy QA**: Customer asks "When will my card refund arrive?" → retrieve "Refund Timelines" chunk from refund policy and answer with the stated 5–7 business days.
- **Troubleshooting**: "App crashes on open" → retrieve troubleshooting steps (update, restart, clear cache, reinstall) and present them in order.
- **Billing dispute**: "Charged twice" → retrieve duplicate-charge guidance distinguishing pending authorization vs posted charge and next actions.

## How This Applies to Our Project
- The **Knowledge Recommendation Agent** uses RAG every customer turn to surface relevant FAQs, policies, and troubleshooting steps in the **Knowledge recommendation panel**.
- **Milestone 1 implementation**: upload (PDF/TXT/MD) → extract (`pypdf`/text) → heading-aware chunking (~450 token target, ~60 overlap) → embed with `all-MiniLM-L6-v2` (local default) → index in **ChromaDB** with metadata → retrieve top-k (default 5) with source, section, and score.
- Retrieved chunks (with sources) are passed to the **Coaching & Response Suggestion Agent** (Milestone 2+) so suggested replies are grounded in KB content.
- A **15-question retrieval test set** (`sample_kb/retrieval_test_set.json`) with expected document/section enables measurement of retrieval quality and tuning (chunk size, overlap, k, query formulation).
- Design choices and rationale are documented in `docs/design_document.md` and `docs/decisions.md`; actual evaluation is captured via `backend/scripts/evaluate_retrieval.py` and `docs/retrieval_test_results.md`.
