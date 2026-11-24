from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Session(Base, TimestampMixin):
    """Interaction session (Simulator, Manual, or Replay)."""
    __tablename__ = "session"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)  # simulator, manual, replay
    product_context: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    persona: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emotional_progression: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)  # created, active, completed, abandoned

    messages: Mapped[List["Message"]] = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    transcript: Mapped[Optional["ReplayTranscript"]] = relationship("ReplayTranscript", back_populates="session", uselist=False, cascade="all, delete-orphan")
    report: Mapped[Optional["SessionReport"]] = relationship("SessionReport", back_populates="session", uselist=False, cascade="all, delete-orphan")

class ReplayTranscript(Base):
    """Uploaded transcript for Replay mode."""
    __tablename__ = "replay_transcript"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("session.id", ondelete="CASCADE"), unique=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="transcript")

class Message(Base):
    """Turn message between customer and agent."""
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("session.id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(20), nullable=False)  # customer, agent
    text: Mapped[str] = mapped_column(Text, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="messages")
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="message", cascade="all, delete-orphan")

class SessionReport(Base):
    """Post-interaction coaching report."""
    __tablename__ = "session_report"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(100), ForeignKey("session.id", ondelete="CASCADE"), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    outcome: Mapped[str] = mapped_column(String(100), nullable=False)
    resolution_score: Mapped[float] = mapped_column(Float, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["Session"] = relationship("Session", back_populates="report")
