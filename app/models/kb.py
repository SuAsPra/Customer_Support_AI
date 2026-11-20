from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class KBDocument(Base, TimestampMixin):
    """Knowledge Base Document metadata and status entity."""
    __tablename__ = "kb_document"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False)  # pdf, markdown, txt
    product_domain: Mapped[str] = mapped_column(String(100), default="ecommerce", nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False, index=True)  # uploaded, indexing, indexed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    chunks: Mapped[List["KBChunk"]] = relationship(
        "KBChunk", back_populates="document", cascade="all, delete-orphan"
    )

class KBChunk(Base):
    """Searchable chunk derived from an ingested document."""
    __tablename__ = "kb_chunk"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kb_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    section: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    page_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["KBDocument"] = relationship("KBDocument", back_populates="chunks")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation", back_populates="chunk", cascade="all, delete-orphan"
    )

class Recommendation(Base):
    """Retrieved chunk associated with a customer message."""
    __tablename__ = "recommendation"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("message.id", ondelete="CASCADE"), nullable=True, index=True
    )
    chunk_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kb_chunk.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    chunk: Mapped["KBChunk"] = relationship("KBChunk", back_populates="recommendations")
    message: Mapped[Optional["Message"]] = relationship("Message", back_populates="recommendations")
