from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session as DBSession
from pathlib import Path
from app.db.database import get_db
from app.models.schemas import KBDocumentOut, RetrieveRequest, RetrieveResponse, RetrieveResult
from app.services import kb_service
from app.rag.vectorstore import query_chunks
from app.core.config import settings

router = APIRouter(prefix="/api/kb", tags=["knowledge-base"])

ALLOWED = {"pdf", "txt", "md"}


@router.post("/documents", response_model=KBDocumentOut)
async def upload_document(file: UploadFile = File(...), db: DBSession = Depends(get_db)):
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED)}")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        path = kb_service.save_upload(content, filename)
        doc = kb_service.create_document(db, filename, str(path), ext)
        doc = kb_service.index_document(db, doc)
        if doc.status == "failed":
            raise HTTPException(status_code=500, detail=doc.error or "Document indexing failed")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload/index failed: {e}")


@router.get("/documents", response_model=list[KBDocumentOut])
def list_documents(db: DBSession = Depends(get_db)):
    return kb_service.list_documents(db)


@router.post("/documents/{doc_id}/reindex", response_model=KBDocumentOut)
def reindex_document(doc_id: str, db: DBSession = Depends(get_db)):
    doc = kb_service.get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = kb_service.index_document(db, doc)
    if doc.status == "failed":
        raise HTTPException(status_code=500, detail=doc.error or "Document indexing failed")
    return doc


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: RetrieveRequest):
    top_k = req.top_k if req.top_k is not None else settings.retrieval_top_k
    raw = query_chunks(req.query, top_k=top_k)
    results = []
    for r in raw:
        meta = r.get("metadata") or {}
        source = meta.get("source") or "unknown"
        # resolve document_id if present
        doc_id = meta.get("document_id") or ""
        results.append(RetrieveResult(
            chunk_id=r.get("chunk_id"),
            document_id=doc_id,
            source=source,
            section=meta.get("section"),
            text=r.get("text") or "",
            score=float(r.get("score") or 0.0),
        ))
    return RetrieveResponse(query=req.query, top_k=top_k, results=results, count=len(results))
