import pytest
from app.services.rag.retriever import KnowledgeRetriever, EmptyQueryError

def test_retriever_query_and_threshold(test_vector_store, embedding_service):
    # Seed vector store with policy chunk
    policy_text = "ApexGear accepts returns of products within thirty (30) days from delivery."
    emb = embedding_service.embed_texts([policy_text])[0]
    test_vector_store.add_chunks(
        chunk_ids=["chunk_1_1"],
        embeddings=[emb],
        documents=[policy_text],
        metadatas=[{
            "chunk_id": 1,
            "document_id": 1,
            "source_filename": "returns.pdf",
            "page_number": 1,
            "section": "Standard 30-Day Return Policy",
            "product_domain": "ecommerce"
        }]
    )

    retriever = KnowledgeRetriever(
        vector_store=test_vector_store,
        embedding_service=embedding_service,
        default_top_k=4,
        default_threshold=0.35
    )

    # Relevant query
    res = retriever.retrieve("How many days do I have to return my purchase?")
    assert res.has_relevant_evidence is True
    assert res.total_results == 1
    assert res.results[0].source_filename == "returns.pdf"
    assert res.results[0].page_number == 1
    assert res.results[0].section == "Standard 30-Day Return Policy"
    assert res.results[0].rank == 1

def test_retriever_no_evidence_fallback(test_vector_store, embedding_service):
    # Seed vector store with electronics policy
    policy_text = "Factory reset requires holding power button for 10 seconds."
    emb = embedding_service.embed_texts([policy_text])[0]
    test_vector_store.add_chunks(
        chunk_ids=["chunk_2_1"],
        embeddings=[emb],
        documents=[policy_text],
        metadatas=[{
            "chunk_id": 2,
            "document_id": 2,
            "source_filename": "tech.pdf",
            "page_number": 1,
            "section": "Reset",
            "product_domain": "ecommerce"
        }]
    )

    retriever = KnowledgeRetriever(
        vector_store=test_vector_store,
        embedding_service=embedding_service,
        default_top_k=4,
        default_threshold=0.70  # Intentionally strict threshold
    )

    # Irrelevant or distant query
    res = retriever.retrieve(
        "Can I book a commercial flight from Tokyo to Paris?",
        score_threshold=0.70
    )
    assert res.has_relevant_evidence is False
    assert len(res.results) == 0
    assert "No relevant evidence found above relevance threshold" in res.message

def test_retriever_empty_query_raises_error(test_vector_store, embedding_service):
    retriever = KnowledgeRetriever(
        vector_store=test_vector_store,
        embedding_service=embedding_service
    )
    with pytest.raises(EmptyQueryError):
        retriever.retrieve("   ")
