import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.kb import KBDocument, KBChunk
from app.schemas.kb import (
    KBDocumentResponse,
    KBDocumentDetailResponse,
    ChunkSummary,
    RetrievalRequest,
    RetrievalResponse,
)
from app.services.rag.pipeline import RAGPipeline, PipelineError
from app.services.rag.retriever import KnowledgeRetriever, EmptyQueryError, RetrievalError
from app.services.rag.extractor import DocumentExtractionError, CorruptedDocumentError, EmptyDocumentError
from app.services.rag.vector_store import get_vector_store
from app.services.rag.embedder import get_embedding_service

logger = logging.getLogger("support_coach.api.kb")

router = APIRouter(prefix="/kb", tags=["Knowledge Base & RAG"])

def get_rag_pipeline() -> RAGPipeline:
    """Dependency provider for RAGPipeline."""
    return RAGPipeline()

def get_knowledge_retriever() -> KnowledgeRetriever:
    """Dependency provider for KnowledgeRetriever."""
    return KnowledgeRetriever()

@router.post(
    "/documents",
    response_model=KBDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest Knowledge Base document"
)
def upload_document(
    file: UploadFile = File(..., description="Document file (PDF, TXT, or MD)"),
    doc_type: Optional[str] = Form(None, description="Optional document type (defaults to file extension)"),
    product_domain: Optional[str] = Form("ecommerce", description="Product domain (e.g. ecommerce, telecom)"),
    db: Session = Depends(get_db),
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Ingests support document into the Knowledge Base:
    - Extracts text with PyPDF
    - Cleans text and retains headings
    - Splits into ~350 token chunks with ~50 token overlap
    - Computes 384-dimensional embeddings via all-MiniLM-L6-v2
    - Persists vectors to ChromaDB and relational metadata to SQLite
    - Skips re-embedding if document hash already exists and is indexed
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file must have a filename.")

    # Infer doc_type if not explicitly passed
    filename_lower = file.filename.lower()
    inferred_type = "pdf"
    if filename_lower.endswith(".pdf"):
        inferred_type = "pdf"
    elif filename_lower.endswith(".md"):
        inferred_type = "markdown"
    elif filename_lower.endswith(".txt"):
        inferred_type = "txt"
    else:
        inferred_type = doc_type or "pdf"

    actual_doc_type = doc_type if doc_type else inferred_type

    try:
        content = file.file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read uploaded file: {str(e)}"
        )

    try:
        doc = pipeline.ingest_document(
            db=db,
            file_bytes=content,
            filename=file.filename,
            doc_type=actual_doc_type,
            product_domain=product_domain or "ecommerce"
        )
        return doc
    except (EmptyDocumentError, CorruptedDocumentError) as de:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(de))
    except PipelineError as pe:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(pe))
    except Exception as e:
        logger.error("Unexpected error ingesting '%s': %s", file.filename, str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Ingestion failed: {str(e)}")

@router.get(
    "/documents",
    response_model=List[KBDocumentResponse],
    summary="List all Knowledge Base documents"
)
def list_documents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (uploaded, indexing, indexed, failed)"),
    product_domain: Optional[str] = Query(None, description="Filter by product domain"),
    db: Session = Depends(get_db)
):
    """Retrieves list of all knowledge base documents with metadata and indexing status."""
    query = db.query(KBDocument)
    if status_filter:
        query = query.filter(KBDocument.status == status_filter)
    if product_domain:
        query = query.filter(KBDocument.product_domain == product_domain)
    return query.order_by(KBDocument.created_at.desc()).all()

@router.get(
    "/documents/{document_id}",
    response_model=KBDocumentDetailResponse,
    summary="Get Knowledge Base document status and chunks"
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Returns document metadata and list of chunk summaries."""
    doc = db.query(KBDocument).filter(KBDocument.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge Base document with ID {document_id} was not found."
        )

    chunks = db.query(KBChunk).filter(KBChunk.document_id == document_id).order_by(KBChunk.chunk_index.asc()).all()
    chunk_summaries = [
        ChunkSummary(
            id=c.id,
            chunk_index=c.chunk_index,
            section=c.section,
            page_number=c.page_number,
            token_count=c.token_count,
            text_preview=c.text[:150] + "..." if len(c.text) > 150 else c.text
        )
        for c in chunks
    ]

    return KBDocumentDetailResponse(
        id=doc.id,
        filename=doc.filename,
        doc_type=doc.doc_type,
        product_domain=doc.product_domain,
        file_hash=doc.file_hash,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks=chunk_summaries
    )

@router.post(
    "/retrieve",
    response_model=RetrievalResponse,
    summary="Retrieve relevant KB chunks for customer query"
)
def retrieve_knowledge(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
    retriever: KnowledgeRetriever = Depends(get_knowledge_retriever)
):
    """
    RAG Retrieval Endpoint:
    - Queries ChromaDB using all-MiniLM-L6-v2 embedding
    - Returns top-k chunks (default: 4)
    - Applies configurable similarity threshold
    - If no relevant evidence passes threshold, returns explicit no-evidence result
    - Grounded with source filename, section, page number, and similarity score
    """
    try:
        response = retriever.retrieve(
            query=request.query,
            db=db,
            product_domain=request.product_domain,
            top_k=request.top_k,
            score_threshold=request.score_threshold
        )
        return response
    except EmptyQueryError as eqe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(eqe))
    except RetrievalError as re:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(re))
    except Exception as e:
        logger.error("Unexpected error in retrieval: %s", str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Retrieval error: {str(e)}")
