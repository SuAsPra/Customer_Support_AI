import hashlib
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.models.kb import KBDocument, KBChunk
from app.services.rag.extractor import (
    DocumentExtractor,
    DocumentExtractionError,
    EmptyDocumentError,
    CorruptedDocumentError
)
from app.services.rag.cleaner import TextCleaner
from app.services.rag.chunker import TextChunker
from app.services.rag.embedder import get_embedding_service, EmbeddingError
from app.services.rag.vector_store import get_vector_store, VectorStoreError

logger = logging.getLogger("support_coach.pipeline")

class PipelineError(Exception):
    """Base exception for RAG ingestion pipeline failures."""
    pass

class RAGPipeline:
    """
    Orchestrates the entire document ingestion and indexing workflow:
    File Upload -> SHA-256 Hash -> PyPDF Extraction -> Text Cleaning ->
    Token-Aware Semantic Chunking -> SentenceTransformers Embeddings ->
    ChromaDB Vector Indexing + SQLite Relational Metadata Persistence.
    """

    def __init__(
        self,
        vector_store=None,
        embedding_service=None,
        chunker=None
    ):
        settings = get_settings()
        self.embedding_service = embedding_service or get_embedding_service()
        self.vector_store = vector_store or get_vector_store()
        self.chunker = chunker or TextChunker(
            target_chunk_size=settings.CHUNK_SIZE_TOKENS,
            chunk_overlap=settings.CHUNK_OVERLAP_TOKENS,
            max_chunk_tokens=getattr(settings, "MAX_CHUNK_TOKENS", 240),
            tokenizer=self.embedding_service.tokenizer
        )

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Computes SHA-256 checksum for document bytes to prevent duplicate indexing."""
        return hashlib.sha256(data).hexdigest()

    def ingest_document(
        self,
        db: Session,
        file_bytes: bytes,
        filename: str,
        doc_type: str = "pdf",
        product_domain: str = "ecommerce",
        force_reindex: bool = False
    ) -> KBDocument:
        """
        Ingests a document into the Knowledge Base.
        Avoids re-embedding unchanged files unless force_reindex=True.
        """
        file_hash = self.compute_sha256(file_bytes)
        logger.info("Ingesting document '%s' (hash: %s, domain: %s, force=%s)...", filename, file_hash, product_domain, force_reindex)

        # Check for existing document with same content hash
        existing_doc = db.query(KBDocument).filter(KBDocument.file_hash == file_hash).first()
        if existing_doc and not force_reindex:
            if existing_doc.status == "indexed":
                logger.info("Document '%s' already indexed (doc_id=%d). Skipping re-embedding.", filename, existing_doc.id)
                return existing_doc
            elif existing_doc.status == "indexing":
                logger.info("Document '%s' is currently being indexed (doc_id=%d).", filename, existing_doc.id)
                return existing_doc
            else:
                # Prior attempt failed; retry by updating existing record
                doc = existing_doc
                doc.status = "indexing"
                doc.error_message = None
                db.commit()
                db.refresh(doc)
        elif existing_doc and force_reindex:
            doc = existing_doc
            doc.status = "indexing"
            doc.error_message = None
            db.commit()
            db.refresh(doc)
        else:
            doc = KBDocument(
                filename=filename,
                doc_type=doc_type,
                product_domain=product_domain,
                file_hash=file_hash,
                status="indexing",
                chunk_count=0
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

        try:
            # 1. Extraction (PyPDF for PDF, text reader for txt/md)
            pages_raw = DocumentExtractor.extract_from_bytes(file_bytes, filename, doc_type)

            # 2. Text Cleaning
            cleaned_pages = []
            for p in pages_raw:
                cleaned_text = TextCleaner.clean(p["text"])
                if cleaned_text:
                    cleaned_pages.append({
                        "page_number": p["page_number"],
                        "text": cleaned_text
                    })

            if not cleaned_pages:
                raise DocumentExtractionError(f"Document '{filename}' contains no meaningful text after cleaning.")

            # 3. Token-Aware Chunking (~400 tokens, ~50 overlap, heading context preservation)
            chunks = self.chunker.chunk_document(cleaned_pages, filename, product_domain)
            if not chunks:
                raise DocumentExtractionError(f"No chunks could be produced from document '{filename}'.")

            chunk_texts = [c.text for c in chunks]

            # 4. Generate Embeddings via all-MiniLM-L6-v2
            embeddings = self.embedding_service.embed_texts(chunk_texts)

            # 5. Index into ChromaDB
            chroma_ids = [f"chunk_{doc.id}_{c.chunk_index}" for c in chunks]
            chroma_metadatas = []
            for c in chunks:
                meta = dict(c.metadata)
                meta["document_id"] = doc.id
                meta["source_filename"] = filename
                meta["product_domain"] = product_domain
                chroma_metadatas.append(meta)

            self.vector_store.add_chunks(
                chunk_ids=chroma_ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=chroma_metadatas
            )

            # 6. Store Chunks in SQLite Relational DB
            # Remove any stale relational chunks for this document
            db.query(KBChunk).filter(KBChunk.document_id == doc.id).delete()

            for c, chroma_id in zip(chunks, chroma_ids):
                db_chunk = KBChunk(
                    document_id=doc.id,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    section=c.section,
                    page_number=c.page_number,
                    token_count=c.token_count,
                    embedding_ref=chroma_id,
                    metadata_json=json.dumps(c.metadata)
                )
                db.add(db_chunk)

            # 7. Mark Document as Indexed
            doc.status = "indexed"
            doc.chunk_count = len(chunks)
            doc.error_message = None
            db.commit()
            db.refresh(doc)

            logger.info("Document '%s' successfully indexed with %d chunks (doc_id=%d).", filename, len(chunks), doc.id)
            return doc

        except (EmptyDocumentError, CorruptedDocumentError) as e:
            db.rollback()
            doc.status = "failed"
            doc.error_message = str(e)
            db.commit()
            db.refresh(doc)
            raise e
        except Exception as e:
            db.rollback()
            error_msg = str(e)
            logger.error("Failed to ingest document '%s': %s", filename, error_msg, exc_info=True)
            doc.status = "failed"
            doc.error_message = error_msg
            db.commit()
            db.refresh(doc)
            # Clean up partial ChromaDB vectors if any were added
            try:
                self.vector_store.delete_document_chunks(doc.id)
            except Exception:
                pass
            raise PipelineError(f"Ingestion failed for '{filename}': {error_msg}")
