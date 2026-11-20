import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.schemas.kb import RetrievalResponse, ChunkResult
from app.services.rag.embedder import get_embedding_service, EmbeddingError
from app.services.rag.vector_store import get_vector_store, VectorStoreError
from app.models.kb import KBChunk

logger = logging.getLogger("support_coach.retriever")

class RetrievalError(Exception):
    """Raised when query retrieval cannot be completed."""
    pass

class EmptyQueryError(RetrievalError):
    """Raised when customer query is empty or whitespace only."""
    pass

class KnowledgeRetriever:
    """
    RAG Retrieval Service.
    Retrieves grounded evidence from knowledge base chunks for customer support queries.
    """

    def __init__(
        self,
        vector_store=None,
        embedding_service=None,
        default_top_k: int = 4,
        default_threshold: float = 0.35
    ):
        settings = get_settings()
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or get_embedding_service()
        self.default_top_k = default_top_k or settings.RETRIEVAL_TOP_K
        self.default_threshold = default_threshold or settings.RETRIEVAL_SIMILARITY_THRESHOLD

    def retrieve(
        self,
        query: str,
        db: Optional[Session] = None,
        product_domain: Optional[str] = None,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None
    ) -> RetrievalResponse:
        """
        Executes semantic retrieval for customer query.
        Validates input, embeds query, queries ChromaDB, checks threshold,
        and returns grounded evidence or explicit no-evidence result.
        """
        if not query or not query.strip():
            raise EmptyQueryError("Retrieval query cannot be empty or whitespace only.")

        clean_query = query.strip()
        k = top_k if top_k is not None and top_k > 0 else self.default_top_k
        threshold = score_threshold if score_threshold is not None else self.default_threshold

        logger.info(
            "Executing retrieval: query='%s', top_k=%d, threshold=%.2f, domain=%s",
            clean_query, k, threshold, product_domain
        )

        # 1. Generate query embedding
        try:
            query_embedding = self.embedding_service.embed_query(clean_query)
        except EmbeddingError as ee:
            logger.error("Failed to generate embedding for query '%s': %s", clean_query, str(ee))
            raise RetrievalError(f"Embedding error during retrieval: {str(ee)}")

        # 2. Query ChromaDB
        where_filter = None
        if product_domain and product_domain.strip():
            where_filter = {"product_domain": product_domain.strip()}

        try:
            raw_results = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=k,
                where_filter=where_filter
            )
        except VectorStoreError as vse:
            logger.error("Vector store search error: %s", str(vse))
            raise RetrievalError(f"Vector database error during retrieval: {str(vse)}")

        if not raw_results:
            logger.info("No vectors found in store matching query.")
            return RetrievalResponse(
                query=clean_query,
                total_results=0,
                has_relevant_evidence=False,
                results=[],
                message="No relevant evidence found in the knowledge base."
            )

        # 3. Filter by relevance threshold and format results
        chunk_results: List[ChunkResult] = []
        filtered_out_count = 0

        for item in raw_results:
            score = item["relevance_score"]
            meta = item["metadata"]

            if score < threshold:
                filtered_out_count += 1
                continue

            # Resolve relational chunk_id if available
            chunk_id_val = meta.get("chunk_id")
            if not chunk_id_val:
                # Parse from chunk_id_str (format: chunk_{doc_id}_{chunk_index})
                chunk_id_str = item.get("chunk_id_str", "")
                parts = chunk_id_str.split("_")
                chunk_id_val = int(parts[-1]) if len(parts) >= 3 and parts[-1].isdigit() else item["rank"]

            document_id_val = int(meta.get("document_id", 0))

            # If DB session provided, optionally verify against relational table
            page_number_val = int(meta.get("page_number", 1))
            section_val = meta.get("section") or "General"
            source_filename_val = meta.get("source_filename") or "unknown.pdf"

            chunk_results.append(
                ChunkResult(
                    chunk_id=int(chunk_id_val),
                    document_id=document_id_val,
                    source_filename=source_filename_val,
                    page_number=page_number_val,
                    section=section_val,
                    text=item["text"],
                    relevance_score=score,
                    distance=item["distance"],
                    rank=len(chunk_results) + 1
                )
            )

        has_evidence = len(chunk_results) > 0
        if has_evidence:
            msg = f"Retrieved {len(chunk_results)} relevant evidence chunk(s) (threshold: {threshold:.2f})."
        else:
            msg = (
                f"No relevant evidence found above relevance threshold of {threshold:.2f} "
                f"({filtered_out_count} candidates scored below threshold)."
            )

        logger.info(
            "Retrieval complete for query '%s': returned %d chunks (has_evidence=%s)",
            clean_query, len(chunk_results), has_evidence
        )

        return RetrievalResponse(
            query=clean_query,
            total_results=len(chunk_results),
            has_relevant_evidence=has_evidence,
            results=chunk_results,
            message=msg
        )
