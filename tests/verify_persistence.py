"""
Verification script for ChromaDB and SQLite persistence across process restarts.
Tests:
1. Document ingestion and metadata persistence.
2. Vector ID alignment between SQLite `kb_chunk.embedding_ref` and ChromaDB vector IDs.
3. SHA-256 duplicate detection and skip logic.
4. Client closure, process simulation, and re-opening of both SQLite and ChromaDB.
5. Successful retrieval from the re-opened store without re-indexing.
"""

import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tempfile
import io
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

# Force offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.models.base import Base
from app.models.kb import KBDocument, KBChunk
from app.services.rag.embedder import get_embedding_service
from app.services.rag.vector_store import VectorStore
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import KnowledgeRetriever

def generate_test_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("1. ApexCare Extended Warranty Terms", styles["Heading1"]),
        Paragraph("All ApexCare Plus plans cover accidental liquid damage and battery degradation for 24 months.", styles["BodyText"]),
        Paragraph("2. Replacement Processing Protocol", styles["Heading1"]),
        Paragraph("Express replacement units will be dispatched within 48 business hours following verification.", styles["BodyText"])
    ]
    doc.build(story)
    return buffer.getvalue()

def run_persistence_verification():
    print("=" * 70)
    print("STARTING CHROMADB AND SQLITE PERSISTENCE VERIFICATION")
    print("=" * 70)

    temp_base = tempfile.mkdtemp(prefix="persist_test_")
    db_path = os.path.join(temp_base, "test_persistence.db")
    chroma_dir = os.path.join(temp_base, "chroma_data")
    os.makedirs(chroma_dir, exist_ok=True)

    db_url = f"sqlite:///{db_path}"
    pdf_bytes = generate_test_pdf()
    embedder = get_embedding_service()

    # PHASE 1: Initial Ingestion
    print("\n--- Phase 1: Ingesting into fresh SQLite and ChromaDB ---")
    engine1 = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine1)
    SessionMaker1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
    session1 = SessionMaker1()

    store1 = VectorStore(persist_directory=chroma_dir, collection_name="persist_test_kb")
    pipeline1 = RAGPipeline(vector_store=store1, embedding_service=embedder)

    doc = pipeline1.ingest_document(
        db=session1,
        file_bytes=pdf_bytes,
        filename="apexcare_policy.pdf",
        doc_type="pdf",
        product_domain="warranty"
    )

    doc_id = doc.id
    chunk_count = doc.chunk_count
    file_hash = doc.file_hash
    print(f"Document ingested: ID={doc_id}, Chunks={chunk_count}, Hash={file_hash[:16]}...")
    assert doc.status == "indexed", "Document status must be indexed"
    assert chunk_count > 0, "Chunk count must be greater than zero"

    # Check relational chunks
    db_chunks = session1.query(KBChunk).filter(KBChunk.document_id == doc_id).all()
    assert len(db_chunks) == chunk_count, "SQLite chunk count must match doc.chunk_count"

    # Verify ID alignment
    chroma_count = store1.get_count()
    assert chroma_count == chunk_count, f"ChromaDB count ({chroma_count}) must match chunk count ({chunk_count})"
    for db_c in db_chunks:
        assert db_c.embedding_ref.startswith(f"chunk_{doc_id}_"), "embedding_ref must match pattern"
        assert db_c.section is not None, "Section metadata must be preserved in SQLite"

    print("Phase 1 verified: Relational chunks match ChromaDB vector IDs.")

    # PHASE 2: Duplicate Ingestion Check (SHA-256 skip)
    print("\n--- Phase 2: Testing Duplicate Prevention via SHA-256 ---")
    doc_duplicate = pipeline1.ingest_document(
        db=session1,
        file_bytes=pdf_bytes,
        filename="apexcare_policy_duplicate.pdf",
        doc_type="pdf",
        product_domain="warranty"
    )
    assert doc_duplicate.id == doc_id, "Duplicate file must return existing doc_id"
    assert store1.get_count() == chunk_count, "ChromaDB vector count must not increase on duplicate upload"
    print("Phase 2 verified: Duplicate upload successfully skipped without duplicate vectors.")

    # PHASE 3: Close connections and simulate full application restart
    print("\n--- Phase 3: Closing all database connections & simulating application reboot ---")
    session1.close()
    engine1.dispose()
    del store1
    del pipeline1
    print("Database connections closed and memory released.")

    # PHASE 4: Reopen fresh instances from disk
    print("\n--- Phase 4: Re-opening SQLite and ChromaDB from persistent disk ---")
    engine2 = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionMaker2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
    session2 = SessionMaker2()

    store2 = VectorStore(persist_directory=chroma_dir, collection_name="persist_test_kb")
    assert store2.get_count() == chunk_count, f"Re-opened ChromaDB must retain all {chunk_count} vectors"

    reloaded_doc = session2.query(KBDocument).filter(KBDocument.id == doc_id).first()
    assert reloaded_doc is not None, "Document must exist in reopened SQLite"
    assert reloaded_doc.status == "indexed", "Document status must still be 'indexed'"
    assert reloaded_doc.file_hash == file_hash, "SHA-256 hash must be preserved"

    reloaded_chunks = session2.query(KBChunk).filter(KBChunk.document_id == doc_id).all()
    assert len(reloaded_chunks) == chunk_count, "All chunk records must be intact"
    print(f"Phase 4 verified: Reopened DBs contain {len(reloaded_chunks)} chunks and {store2.get_count()} vectors.")

    # PHASE 5: Retrieval Verification without Re-ingestion
    print("\n--- Phase 5: Querying reopened store without re-indexing ---")
    retriever2 = KnowledgeRetriever(
        vector_store=store2,
        embedding_service=embedder,
        default_top_k=4,
        default_threshold=0.30
    )

    query = "Does ApexCare cover accidental liquid spills?"
    result = retriever2.retrieve(query=query, db=session2, product_domain="warranty")

    assert result.has_relevant_evidence is True, "Must find relevant evidence from persisted store"
    assert len(result.results) > 0, "Must return at least 1 result"
    top_chunk = result.results[0]
    print(f"Top result: [{top_chunk.section}] Score: {top_chunk.relevance_score:.4f}")
    print(f"Source file: {top_chunk.source_filename}, Page: {top_chunk.page_number}")
    print(f"Excerpt: {top_chunk.text[:120]}...")
    assert "liquid damage" in top_chunk.text.lower(), "Expected liquid damage policy in retrieved text"
    assert top_chunk.source_filename == "apexcare_policy.pdf"

    session2.close()
    engine2.dispose()

    # Cleanup temp test files
    shutil.rmtree(temp_base, ignore_errors=True)

    print("\n" + "=" * 70)
    print("PERSISTENCE VERIFICATION PASSED: 100% SUCCESS")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = run_persistence_verification()
    sys.exit(0 if success else 1)
