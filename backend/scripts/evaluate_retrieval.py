"""
Run retrieval evaluation against sample_kb/retrieval_test_set.json.

Usage (from repo root, after installing deps and starting/indexing KB OR using direct indexing):
  python backend/scripts/evaluate_retrieval.py

This script indexes sample_kb/shopnest/*.md into the configured vector store (same as app)
and queries each test question, then writes results to docs/retrieval_test_results.md.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.rag.extract import extract_text  # noqa: E402
from app.rag.chunk import chunk_text  # noqa: E402
from app.rag.vectorstore import index_chunks, query_chunks  # noqa: E402


def matches_expected_result(
    metadata: dict,
    expected_document: str | None,
    expected_section: str,
) -> bool:
    source = str(metadata.get("source") or "")
    section = str(metadata.get("section") or "").lower()
    document_matches = (
        expected_document is None
        or expected_document in source
        or source in expected_document
    )
    section_matches = (
        not expected_section
        or (
            bool(section)
            and (expected_section in section or section in expected_section)
        )
    )
    return document_matches and section_matches


def index_sample_kb():
    sample_dir = ROOT / "sample_kb" / "shopnest"
    files = sorted(sample_dir.glob("*.md"))
    all_chunks = []
    for fp in files:
        text = extract_text(fp, "md")
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap, source=fp.name)
        for ch in chunks:
            cid = f"{fp.stem}_{ch.index}"
            meta = {**(ch.metadata or {}), "document_id": fp.stem, "source": fp.name, "chunk_index": ch.index}
            all_chunks.append({"id": cid, "text": ch.text, "metadata": meta})
    if all_chunks:
        index_chunks(all_chunks)
    return len(files), len(all_chunks)


def run_eval(top_k: int = 5):
    test_path = ROOT / "sample_kb" / "retrieval_test_set.json"
    tests = json.loads(test_path.read_text(encoding="utf-8"))
    results = []
    hits = 0
    for t in tests:
        q = t["question"]
        expected_doc = t.get("expected_document")
        expected_section = (t.get("expected_section") or "").lower()
        retrieved = query_chunks(q, top_k=top_k)
        found = False
        matched_rank = None
        top_source = None
        top_section = None
        top_score = None
        if retrieved:
            top_source = (retrieved[0].get("metadata") or {}).get("source")
            top_section = (retrieved[0].get("metadata") or {}).get("section")
            top_score = retrieved[0].get("score")
        for i, r in enumerate(retrieved, start=1):
            meta = r.get("metadata") or {}
            if matches_expected_result(meta, expected_doc, expected_section):
                found = True
                matched_rank = i
                break
        if found:
            hits += 1
        results.append({
            **t,
            "found_in_top_k": found,
            "matched_rank": matched_rank,
            "top_source": top_source,
            "top_section": top_section,
            "top_score": top_score,
            "retrieved": [
                {
                    "rank": i + 1,
                    "source": (r.get("metadata") or {}).get("source"),
                    "section": (r.get("metadata") or {}).get("section"),
                    "score": r.get("score"),
                    "snippet": (r.get("text") or "")[:180].replace("\n", " ") + ("..." if len(r.get("text") or "") > 180 else "")
                }
                for i, r in enumerate(retrieved)
            ]
        })
    summary = {
        "total": len(tests),
        "hits_in_top_k": hits,
        "hit_rate": round(hits / len(tests), 4) if tests else 0,
        "top_k": top_k,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "embedding_provider": settings.embedding_provider,
        "embedding_model": settings.embedding_model,
    }
    return summary, results


def write_report(summary, results, out_path: Path):
    lines = []
    lines.append("# Retrieval Test Results (Milestone 1)")
    lines.append("")
    lines.append("## Configuration")
    lines.append(f"- Embedding: `{summary['embedding_provider']}` / `{summary['embedding_model']}`")
    lines.append(f"- Chunk size (token target): {summary['chunk_size']}, overlap: {summary['chunk_overlap']}")
    lines.append(f"- Top-k: {summary['top_k']}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Total questions: **{summary['total']}**")
    lines.append(f"- Expected doc/section found in top-{summary['top_k']}: **{summary['hits_in_top_k']}**")
    lines.append(f"- Hit rate: **{summary['hit_rate']*100:.1f}%**")
    lines.append("")
    lines.append("## Per-question Results")
    lines.append("")
    lines.append("| # | Question | Expected (doc / section) | Found? | Rank | Top result (source / section / score) |")
    lines.append("|---:|---|---|:---:|---:|---|")
    for r in results:
        found = "Yes" if r["found_in_top_k"] else "No"
        rank = r["matched_rank"] if r["matched_rank"] else "-"
        top = f"{r.get('top_source')} / {r.get('top_section')} / {r.get('top_score')}"
        q = r["question"].replace("|", "\\|")
        exp = f"{r.get('expected_document')} / {r.get('expected_section')}"
        lines.append(f"| {r['id']} | {q} | {exp} | {found} | {rank} | {top} |")
    lines.append("")
    lines.append("## Retrieved snippets (top result per question)")
    for r in results:
        lines.append(f"### Q{r['id']}: {r['question']}")
        if r["retrieved"]:
            top = r["retrieved"][0]
            lines.append(f"- **Top-1**: `{top['source']}` | {top['section']} | score={top['score']}")
            lines.append(f"- Snippet: {top['snippet']}")
        else:
            lines.append("- No results")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    # fresh collection for evaluation run isolation is not enforced; this uses configured store
    n_docs, n_chunks = index_sample_kb()
    summary, results = run_eval(top_k=settings.retrieval_top_k)
    out = ROOT / "docs" / "retrieval_test_results.md"
    write_report(summary, results, out)
    print(json.dumps({"indexed_docs": n_docs, "indexed_chunks": n_chunks, **summary}, indent=2))
    print(f"Wrote: {out}")
