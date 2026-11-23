from __future__ import annotations
import chromadb
from pathlib import Path
from typing import Any
from app.core.config import settings

_client = None
_collection = None


def _get_embedding_function():
    provider = (settings.embedding_provider or "sentence-transformers").lower()
    if provider == "sentence-transformers":
        from chromadb.utils import embedding_functions
        return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")


def get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection
    persist_dir = Path(settings.chroma_persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)
    _client = chromadb.PersistentClient(path=str(persist_dir))
    ef = _get_embedding_function()
    _collection = _client.get_or_create_collection(name="kb_chunks", embedding_function=ef, metadata={"hnsw:space": "cosine"})
    return _collection


def index_chunks(chunks: list[dict[str, Any]]):
    """chunks: [{id, text, metadata}]"""
    if not chunks:
        return 0
    col = get_collection()
    ids = [c["id"] for c in chunks]
    docs = [c["text"] for c in chunks]
    metas = [c.get("metadata") or {} for c in chunks]
    # upsert in batches
    batch = 100
    for i in range(0, len(ids), batch):
        col.upsert(ids=ids[i:i+batch], documents=docs[i:i+batch], metadatas=metas[i:i+batch])
    return len(ids)


def query_chunks(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    col = get_collection()
    if col.count() == 0:
        return []
    res = col.query(query_texts=[query], n_results=top_k, include=["documents", "metadatas", "distances"])
    results = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]
    for cid, doc, meta, dist in zip(ids, docs, metas, dists):
        # cosine distance -> similarity-ish score
        try:
            score = 1.0 - float(dist)
        except Exception:
            score = 0.0
        results.append({"chunk_id": cid, "text": doc, "metadata": meta or {}, "score": round(score, 4)})
    return results


def delete_document_chunks(document_id: str):
    col = get_collection()
    col.delete(where={"document_id": document_id})
