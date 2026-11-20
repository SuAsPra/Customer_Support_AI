"""
Retrieval Evaluation Script for AI Customer Support Coaching Assistant - Milestone 1
Evaluates the RAG pipeline against the 16 customer questions test set.
Computes Top-1 Accuracy, Top-4 Recall, MRR, and Keyword Coverage.
"""
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, init_db
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import KnowledgeRetriever

def run_evaluation():
    print("=" * 80)
    print("RAG PIPELINE RETRIEVAL EVALUATION - MILESTONE 1")
    print("=" * 80)

    # 1. Initialize Database & Pipeline
    init_db()
    db = SessionLocal()
    pipeline = RAGPipeline()
    retriever = KnowledgeRetriever()

    # 2. Ingest Sample Documents
    sample_docs_dir = PROJECT_ROOT / "data" / "sample_docs"
    sample_files = [
        "returns_and_refunds_policy.pdf",
        "hardware_troubleshooting_guide.pdf",
        "shipping_and_delivery_policy.pdf",
        "billing_and_warranty_faq.pdf"
    ]

    print("\n[Step 1] Ingesting sample knowledge base documents...")
    for filename in sample_files:
        filepath = sample_docs_dir / filename
        if not filepath.exists():
            print(f"Error: Sample file '{filepath}' not found. Please generate sample PDFs first.")
            return

        with open(filepath, "rb") as f:
            content = f.read()

        doc = pipeline.ingest_document(
            db=db,
            file_bytes=content,
            filename=filename,
            doc_type="pdf",
            product_domain="ecommerce",
            force_reindex=True
        )
        print(f"  ✓ {filename:<36} -> Status: {doc.status:<8} Chunks: {doc.chunk_count}")

    # 3. Load Test Questions
    test_file = PROJECT_ROOT / "data" / "evaluation" / "test_questions.json"
    with open(test_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    print(f"\n[Step 2] Evaluating retrieval across {len(questions)} customer test questions...")

    top1_doc_hits = 0
    top4_doc_hits = 0
    top1_sec_hits = 0
    top4_sec_hits = 0
    keyword_hits = 0
    reciprocal_ranks = []
    scores = []

    print("-" * 80)
    print(f"{'ID':<4} | {'Expected Doc':<30} | {'Top-1 Retr Doc':<30} | {'Score':<6} | {'Doc Hit':<7} | {'Sec Hit'}")
    print("-" * 80)

    for q in questions:
        q_id = q["id"]
        query_text = q["customer_question"]
        expected_doc = q["expected_document"]
        expected_sec = q["expected_section"].lower()
        expected_kws = [kw.lower() for kw in q.get("expected_keywords", [])]

        response = retriever.retrieve(query=query_text, db=db, top_k=4, score_threshold=0.30)
        results = response.results

        # Evaluate Document Matches
        top1_doc = results[0].source_filename if results else "None"
        top1_sec = (results[0].section or "").lower() if results else ""
        top1_score = results[0].relevance_score if results else 0.0

        is_top1_doc_match = (top1_doc == expected_doc)
        is_top4_doc_match = any(r.source_filename == expected_doc for r in results)

        # Section Matches (check substring or section title)
        sec_clean = expected_sec.split(". ", 1)[-1].strip()
        is_top1_sec_match = (sec_clean in top1_sec or top1_sec in expected_sec)
        is_top4_sec_match = any(sec_clean in (r.section or "").lower() or (r.section or "").lower() in expected_sec for r in results)

        # Keyword Coverage in top-4
        all_retrieved_text = " ".join(r.text.lower() for r in results)
        kw_matched = any(kw in all_retrieved_text for kw in expected_kws)

        # MRR calculation
        rank_for_doc = 0
        for idx, r in enumerate(results, start=1):
            if r.source_filename == expected_doc and (sec_clean in (r.section or "").lower() or is_top4_sec_match):
                rank_for_doc = idx
                break
        if rank_for_doc > 0:
            reciprocal_ranks.append(1.0 / rank_for_doc)
        else:
            reciprocal_ranks.append(0.0)

        if is_top1_doc_match:
            top1_doc_hits += 1
        if is_top4_doc_match:
            top4_doc_hits += 1
        if is_top1_sec_match:
            top1_sec_hits += 1
        if is_top4_sec_match:
            top4_sec_hits += 1
        if kw_matched:
            keyword_hits += 1
        if results:
            scores.append(top1_score)

        print(
            f"{q_id:<4} | {expected_doc[:30]:<30} | {top1_doc[:30]:<30} | "
            f"{top1_score:<6.3f} | {('✓' if is_top1_doc_match else '✗'):<7} | "
            f"{('✓' if is_top1_sec_match else '✗')}"
        )

    # 4. Summary Metrics
    total = len(questions)
    top1_doc_acc = (top1_doc_hits / total) * 100
    top4_doc_rec = (top4_doc_hits / total) * 100
    top1_sec_acc = (top1_sec_hits / total) * 100
    top4_sec_rec = (top4_sec_hits / total) * 100
    kw_rate = (keyword_hits / total) * 100
    mrr = (sum(reciprocal_ranks) / total) if total else 0.0
    avg_score = (sum(scores) / len(scores)) if scores else 0.0

    print("=" * 80)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Test Questions:        {total}")
    print(f"Top-1 Document Accuracy:     {top1_doc_acc:.1f}% ({top1_doc_hits}/{total})")
    print(f"Top-4 Document Recall:       {top4_doc_rec:.1f}% ({top4_doc_hits}/{total})")
    print(f"Top-1 Section Accuracy:      {top1_sec_acc:.1f}% ({top1_sec_hits}/{total})")
    print(f"Top-4 Section Recall:        {top4_sec_rec:.1f}% ({top4_sec_hits}/{total})")
    print(f"Keyword Coverage Rate:       {kw_rate:.1f}% ({keyword_hits}/{total})")
    print(f"Mean Reciprocal Rank (MRR):  {mrr:.3f}")
    print(f"Average Top-1 Score:         {avg_score:.3f}")
    print("=" * 80)

    db.close()
    return {
        "top1_doc_acc": top1_doc_acc,
        "top4_doc_rec": top4_doc_rec,
        "top1_sec_acc": top1_sec_acc,
        "top4_sec_rec": top4_sec_rec,
        "mrr": mrr,
        "avg_score": avg_score
    }

if __name__ == "__main__":
    run_evaluation()
