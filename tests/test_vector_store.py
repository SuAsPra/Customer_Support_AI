from app.services.rag.vector_store import VectorStore

def test_vector_store_add_and_search(test_vector_store, embedding_service):
    doc_text = "ApexPro headphones feature an IPX4 water resistance rating."
    emb = embedding_service.embed_texts([doc_text])[0]

    test_vector_store.add_chunks(
        chunk_ids=["chunk_1_0"],
        embeddings=[emb],
        documents=[doc_text],
        metadatas=[{
            "document_id": 1,
            "source_filename": "guide.pdf",
            "page_number": 1,
            "section": "Water Resistance"
        }]
    )

    assert test_vector_store.get_count() == 1

    # Search with matching query
    q_emb = embedding_service.embed_query("Can I take my headphones in the swimming pool?")
    results = test_vector_store.search(q_emb, top_k=2)
    assert len(results) == 1
    assert results[0]["chunk_id_str"] == "chunk_1_0"
    assert results[0]["relevance_score"] > 0.3
    assert results[0]["metadata"]["source_filename"] == "guide.pdf"

def test_vector_store_duplicate_prevention(test_vector_store, embedding_service):
    doc_text = "Return window is 30 days."
    emb = embedding_service.embed_texts([doc_text])[0]

    # Add twice with same ID
    test_vector_store.add_chunks(
        chunk_ids=["chunk_1_0"],
        embeddings=[emb],
        documents=[doc_text],
        metadatas=[{"document_id": 1}]
    )
    test_vector_store.add_chunks(
        chunk_ids=["chunk_1_0"],
        embeddings=[emb],
        documents=[doc_text],
        metadatas=[{"document_id": 1}]
    )

    # Upsert ensures total count is still 1
    assert test_vector_store.get_count() == 1

def test_vector_store_persistence(temp_chroma_dir, embedding_service):
    doc_text = "Persistent test document."
    emb = embedding_service.embed_texts([doc_text])[0]

    # Store in first client instance
    store1 = VectorStore(persist_directory=temp_chroma_dir, collection_name="persist_col")
    store1.add_chunks(
        chunk_ids=["p_1"],
        embeddings=[emb],
        documents=[doc_text],
        metadatas=[{"document_id": 99}]
    )
    assert store1.get_count() == 1

    # Open with second client instance pointing to same directory
    store2 = VectorStore(persist_directory=temp_chroma_dir, collection_name="persist_col")
    assert store2.get_count() == 1
    q_emb = embedding_service.embed_query("Persistent test")
    results = store2.search(q_emb, top_k=1)
    assert len(results) == 1
    assert results[0]["chunk_id_str"] == "p_1"

def test_vector_store_delete_document_chunks(test_vector_store, embedding_service):
    emb = embedding_service.embed_texts(["Test"])[0]
    test_vector_store.add_chunks(
        chunk_ids=["c_1", "c_2"],
        embeddings=[emb, emb],
        documents=["Doc 1 chunk", "Doc 2 chunk"],
        metadatas=[{"document_id": 10}, {"document_id": 20}]
    )
    assert test_vector_store.get_count() == 2
    test_vector_store.delete_document_chunks(document_id=10)
    assert test_vector_store.get_count() == 1
