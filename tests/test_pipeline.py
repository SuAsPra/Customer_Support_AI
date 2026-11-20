from app.models.kb import KBDocument, KBChunk
from app.services.rag.pipeline import RAGPipeline

def test_pipeline_ingest_and_deduplication(db_session, test_vector_store, embedding_service, sample_pdf_bytes):
    pipeline = RAGPipeline(
        vector_store=test_vector_store,
        embedding_service=embedding_service
    )

    # First ingestion
    doc1 = pipeline.ingest_document(
        db=db_session,
        file_bytes=sample_pdf_bytes,
        filename="warranty_and_return.pdf",
        doc_type="pdf",
        product_domain="ecommerce"
    )
    assert doc1.status == "indexed"
    assert doc1.chunk_count > 0

    # Verify relational db chunks stored
    db_chunks = db_session.query(KBChunk).filter(KBChunk.document_id == doc1.id).all()
    assert len(db_chunks) == doc1.chunk_count
    # Verify vector store
    assert test_vector_store.get_count() == doc1.chunk_count

    # Second ingestion of the EXACT same file (same SHA-256)
    doc2 = pipeline.ingest_document(
        db=db_session,
        file_bytes=sample_pdf_bytes,
        filename="warranty_and_return_duplicate.pdf",
        doc_type="pdf",
        product_domain="ecommerce"
    )
    # Must reuse existing doc and NOT double-insert chunks into ChromaDB
    assert doc2.id == doc1.id
    assert test_vector_store.get_count() == doc1.chunk_count

def test_pipeline_corrupted_file_marks_status_failed(db_session, test_vector_store, embedding_service, corrupted_pdf_bytes):
    pipeline = RAGPipeline(
        vector_store=test_vector_store,
        embedding_service=embedding_service
    )
    try:
        pipeline.ingest_document(
            db=db_session,
            file_bytes=corrupted_pdf_bytes,
            filename="corrupted.pdf",
            doc_type="pdf"
        )
    except Exception:
        pass

    # Verify failure record in relational DB
    failed_doc = db_session.query(KBDocument).filter(KBDocument.filename == "corrupted.pdf").first()
    assert failed_doc is not None
    assert failed_doc.status == "failed"
    assert failed_doc.error_message is not None
    assert test_vector_store.get_count() == 0
