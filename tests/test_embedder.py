import math
import pytest
from app.services.rag.embedder import EmbeddingService, EmbeddingError

def test_embed_texts_dimension_and_normalization(embedding_service):
    texts = [
        "How do I return my damaged headphones?",
        "What is the warranty period for ApexBuds?"
    ]
    embeddings = embedding_service.embed_texts(texts)
    assert len(embeddings) == 2
    for emb in embeddings:
        assert len(emb) == 384
        # Verify unit norm: sum of squares equals 1.0 (within float tolerance)
        norm = math.sqrt(sum(x * x for x in emb))
        assert pytest.approx(norm, abs=1e-4) == 1.0

def test_embed_query_symmetry(embedding_service):
    query = "returns policy"
    q_emb = embedding_service.embed_query(query)
    c_emb = embedding_service.embed_texts([query])[0]
    assert len(q_emb) == 384
    # Query and chunk embeddings for same text must match exactly
    for q_val, c_val in zip(q_emb, c_emb):
        assert pytest.approx(q_val, abs=1e-5) == c_val

def test_embed_empty_query_raises_error(embedding_service):
    with pytest.raises(EmbeddingError):
        embedding_service.embed_query("   ")
