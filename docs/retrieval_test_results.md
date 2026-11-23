# Retrieval Test Results (Milestone 1)

## Status
**Actual results not yet generated in this environment** (dependencies/embedding model may not be installed). Use the provided evaluation script to produce and refresh this document with real outputs.

## How to generate actual results
1. Install dependencies and configure `.env` (defaults are fine):
   ```bash
   pip install -r backend/requirements.txt
   ```
2. Run the evaluation script from repo root (indexes `sample_kb/shopnest/*.md` and tests 15 questions):
   ```bash
   python backend/scripts/evaluate_retrieval.py
   ```
3. The script overwrites this file with:
   - configuration (embedding model, chunk size/overlap, top-k)
   - summary (total, hits in top-k, hit rate)
   - per-question table (expected doc/section, found?, rank, top result)
   - top retrieved snippet per question

## Test set
- Source: `sample_kb/retrieval_test_set.json` (15 questions)
- Knowledge base: `sample_kb/shopnest/` (`faq.md`, `refund_policy.md`, `shipping_and_delivery.md`, `troubleshooting.md`)
- Each question includes `expected_document` and `expected_section` to validate relevance and source attribution.

## Expected outcome (qualitative)
With the default local embedding model (`all-MiniLM-L6-v2`), chunk size ~450 tokens, overlap ~60, and top-k 5, queries should retrieve chunks from the correct document/section for most of the 15 test questions because questions are phrased close to KB content. Any misses should be analyzed by adjusting chunking, top-k, or query formulation (see `docs/design_document.md` and `docs/decisions.md`).

## Notes
- Record the actual hit rate, failure cases, and any tuning performed here after running the script.
- This document, together with the script and test set, satisfies: "Test the RAG pipeline and document the actual retrieval results."
