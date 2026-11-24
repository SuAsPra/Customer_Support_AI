import io
import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# Force offline mode so SentenceTransformers never tries to reach HuggingFace Hub
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

from app.models.base import Base
import app.models.kb
import app.models.session
from app.database import get_db
from app.main import app
from app.services.rag.embedder import get_embedding_service
from app.services.rag.vector_store import VectorStore
from app.services.rag.pipeline import RAGPipeline
from app.services.rag.retriever import KnowledgeRetriever
from app.api.v1.endpoints.kb import get_rag_pipeline, get_knowledge_retriever

@pytest.fixture(scope="session")
def embedding_service():
    """Provides singleton SentenceTransformers embedder."""
    return get_embedding_service()

@pytest.fixture
def temp_chroma_dir():
    """Provides a fresh isolated temporary directory for ChromaDB in each test."""
    temp_dir = tempfile.mkdtemp(prefix="test_chroma_")
    yield temp_dir
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

@pytest.fixture
def test_vector_store(temp_chroma_dir):
    """Provides an isolated VectorStore instance."""
    store = VectorStore(
        persist_directory=temp_chroma_dir,
        collection_name="test_kb_collection"
    )
    yield store
    try:
        store.reset_collection()
    except Exception:
        pass

from sqlalchemy.pool import StaticPool

@pytest.fixture
def db_session():
    """Provides an isolated SQLite database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client(db_session, test_vector_store, embedding_service):
    """Provides FastAPI test client overriding database, pipeline, and retriever dependencies."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_rag_pipeline():
        return RAGPipeline(
            vector_store=test_vector_store,
            embedding_service=embedding_service
        )

    def override_get_knowledge_retriever():
        return KnowledgeRetriever(
            vector_store=test_vector_store,
            embedding_service=embedding_service
        )

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_rag_pipeline] = override_get_rag_pipeline
    app.dependency_overrides[get_knowledge_retriever] = override_get_knowledge_retriever

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def sample_pdf_bytes():
    """Generates valid 2-page sample PDF bytes for testing."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("1. Warranty and Return Terms", styles["Heading1"]),
        Paragraph("All devices include a standard one-year replacement warranty covering manufacturing defects.", styles["BodyText"]),
        Paragraph("Returns must be initiated within 30 days of package receipt in original packaging.", styles["BodyText"]),
        PageBreak(),
        Paragraph("2. Technical Support Guidelines", styles["Heading1"]),
        Paragraph("For hardware issues, perform a factory reset by holding down power for 10 seconds.", styles["BodyText"])
    ]
    doc.build(story)
    return buffer.getvalue()

@pytest.fixture
def empty_pdf_bytes():
    """Generates an empty PDF with pages but no extractable text."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    doc.build([PageBreak()])
    return buffer.getvalue()

@pytest.fixture
def corrupted_pdf_bytes():
    """Returns invalid/corrupted bytes."""
    return b"%PDF-1.4\nCorrupted binary garbage without valid xref table"
