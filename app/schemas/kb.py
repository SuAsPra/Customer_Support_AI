from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class ChunkSummary(BaseModel):
    id: int
    chunk_index: int
    section: Optional[str] = None
    page_number: int = 1
    token_count: int
    text_preview: str

class KBDocumentResponse(BaseModel):
    id: int
    filename: str
    doc_type: str
    product_domain: str
    file_hash: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KBDocumentDetailResponse(KBDocumentResponse):
    chunks: List[ChunkSummary] = []

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Customer question or support query")
    product_domain: Optional[str] = Field(None, description="Optional product context filter")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of chunks to retrieve (default: 4)")
    score_threshold: float = Field(
        default=0.35, ge=0.0, le=1.0, description="Minimum similarity score threshold (default: 0.35)"
    )

class ChunkResult(BaseModel):
    chunk_id: int = Field(..., description="Relational ID of the KBChunk")
    document_id: int = Field(..., description="ID of source KBDocument")
    source_filename: str = Field(..., description="Original filename of the document")
    page_number: int = Field(..., description="Page number where the chunk originated")
    section: Optional[str] = Field(None, description="Section heading context")
    text: str = Field(..., description="Extracted chunk text")
    relevance_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    distance: float = Field(..., description="ChromaDB cosine distance metric")
    rank: int = Field(..., description="Retrieval rank order (1-indexed)")

class RetrievalResponse(BaseModel):
    query: str
    total_results: int
    has_relevant_evidence: bool
    results: List[ChunkResult]
    message: str
