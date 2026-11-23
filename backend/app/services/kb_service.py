from pathlib import Path
from sqlalchemy.orm import Session as DBSession
from app.core.config import settings
from app.db import models
from app.rag.extract import extract_text
from app.rag.chunk import chunk_text
from app.rag.vectorstore import index_chunks, delete_document_chunks


def save_upload(file_bytes: bytes, filename: str) -> Path:
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(filename).name.replace("..", "_")
    path = upload_dir / safe_name
    # avoid overwrite collisions
    if path.exists():
        stem, suf = path.stem, path.suffix
        i = 1
        while path.exists():
            path = upload_dir / f"{stem}_{i}{suf}"
            i += 1
    path.write_bytes(file_bytes)
    return path


def create_document(db: DBSession, filename: str, file_path: str, file_type: str) -> models.KBDocument:
    doc = models.KBDocument(filename=filename, file_path=str(file_path), file_type=file_type, status="uploaded", chunk_count=0)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def index_document(db: DBSession, doc: models.KBDocument) -> models.KBDocument:
    try:
        text = extract_text(doc.file_path, doc.file_type)
        if not text.strip():
            if doc.chunk_count:
                delete_document_chunks(doc.id)
            db.query(models.KBChunk).filter(models.KBChunk.document_id == doc.id).delete()
            doc.status = "failed"
            doc.error = "No extractable text found"
            doc.chunk_count = 0
            db.commit()
            db.refresh(doc)
            return doc
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap, source=doc.filename)
        # clear old
        delete_document_chunks(doc.id)
        db.query(models.KBChunk).filter(models.KBChunk.document_id == doc.id).delete()
        db.commit()

        vec_payload = []
        for ch in chunks:
            kb_chunk = models.KBChunk(document_id=doc.id, chunk_index=ch.index, text=ch.text, meta=ch.metadata)
            db.add(kb_chunk)
            db.flush()  # get id
            kb_chunk.embedding_ref = kb_chunk.id
            meta = {**(ch.metadata or {}), "document_id": doc.id, "chunk_db_id": kb_chunk.id, "chunk_index": ch.index}
            vec_payload.append({"id": kb_chunk.id, "text": ch.text, "metadata": meta})
        db.commit()

        index_chunks(vec_payload)
        doc.status = "indexed"
        doc.chunk_count = len(chunks)
        doc.error = None
        db.commit()
        db.refresh(doc)
        return doc
    except Exception as e:
        db.rollback()
        cleanup_error = None
        try:
            delete_document_chunks(doc.id)
        except Exception as cleanup_exception:
            cleanup_error = f"; vector cleanup failed: {cleanup_exception}"
        db.query(models.KBChunk).filter(models.KBChunk.document_id == doc.id).delete()
        doc.status = "failed"
        doc.error = f"{e}{cleanup_error or ''}"
        doc.chunk_count = 0
        db.commit()
        db.refresh(doc)
        return doc


def list_documents(db: DBSession):
    return db.query(models.KBDocument).order_by(models.KBDocument.upload_time.desc()).all()


def get_document(db: DBSession, doc_id: str):
    return db.query(models.KBDocument).filter(models.KBDocument.id == doc_id).first()
