from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import Base
from app.db.models import KBDocument, KBChunk
from app.services import kb_service


def test_failed_index_clears_unsearchable_chunk_rows(monkeypatch, tmp_path):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)

    def extract_text(path, file_type):
        assert path == str(tmp_path / "faq.md")
        assert file_type == "md"
        return "A support answer."

    def delete_document_chunks(document_id):
        assert document_id == "doc-id"

    def fail_index_chunks(chunks):
        assert chunks
        raise RuntimeError("embedding failed")

    monkeypatch.setattr(kb_service, "extract_text", extract_text)
    monkeypatch.setattr(kb_service, "delete_document_chunks", delete_document_chunks)
    monkeypatch.setattr(kb_service, "index_chunks", fail_index_chunks)

    with Session(engine) as db:
        doc = KBDocument(
            id="doc-id",
            filename="faq.md",
            file_type="md",
            file_path=str(tmp_path / "faq.md"),
            status="uploaded",
            chunk_count=0,
        )
        db.add(doc)
        db.commit()

        result = kb_service.index_document(db, doc)

        assert result.status == "failed"
        assert result.error == "embedding failed"
        assert result.chunk_count == 0
        assert db.query(KBChunk).filter(KBChunk.document_id == doc.id).count() == 0
