import pytest

def test_api_upload_document(client, sample_pdf_bytes):
    response = client.post(
        "/api/kb/documents",
        files={"file": ("returns_policy.pdf", sample_pdf_bytes, "application/pdf")},
        data={"doc_type": "pdf", "product_domain": "ecommerce"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "returns_policy.pdf"
    assert data["status"] == "indexed"
    assert data["chunk_count"] > 0
    assert "file_hash" in data

def test_api_upload_corrupted_document(client, corrupted_pdf_bytes):
    response = client.post(
        "/api/kb/documents",
        files={"file": ("corrupted.pdf", corrupted_pdf_bytes, "application/pdf")},
        data={"doc_type": "pdf", "product_domain": "ecommerce"}
    )
    assert response.status_code == 422
    assert "Corrupted or invalid" in response.json()["detail"]

def test_api_list_and_get_document(client, sample_pdf_bytes):
    # Upload one document
    upload_res = client.post(
        "/api/kb/documents",
        files={"file": ("guide.pdf", sample_pdf_bytes, "application/pdf")},
        data={"doc_type": "pdf", "product_domain": "ecommerce"}
    )
    doc_id = upload_res.json()["id"]

    # List documents
    list_res = client.get("/api/kb/documents")
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) >= 1
    assert any(d["id"] == doc_id for d in docs)

    # Get document detail
    detail_res = client.get(f"/api/kb/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == doc_id
    assert len(detail["chunks"]) == detail["chunk_count"]
    assert detail["chunks"][0]["section"] is not None

def test_api_get_nonexistent_document(client):
    res = client.get("/api/kb/documents/999999")
    assert res.status_code == 404

def test_api_retrieve(client, sample_pdf_bytes):
    # Ingest document first
    client.post(
        "/api/kb/documents",
        files={"file": ("support.pdf", sample_pdf_bytes, "application/pdf")},
        data={"doc_type": "pdf", "product_domain": "ecommerce"}
    )

    # Retrieve matching query
    retrieve_payload = {
        "query": "How do I factory reset my hardware?",
        "product_domain": "ecommerce",
        "top_k": 2,
        "score_threshold": 0.30
    }
    res = client.post("/api/kb/retrieve", json=retrieve_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == retrieve_payload["query"]
    assert data["has_relevant_evidence"] is True
    assert len(data["results"]) > 0
    assert data["results"][0]["source_filename"] == "support.pdf"
    assert data["results"][0]["page_number"] > 0
    assert "factory reset" in data["results"][0]["text"].lower()

def test_api_retrieve_empty_query_validation(client):
    res = client.post("/api/kb/retrieve", json={"query": ""})
    assert res.status_code == 422  # Pydantic min_length validation

def test_api_retrieve_no_evidence(client):
    # Strict threshold on query with nothing in DB
    retrieve_payload = {
        "query": "Can you book a submarine tour in the Atlantic ocean?",
        "top_k": 2,
        "score_threshold": 0.85
    }
    res = client.post("/api/kb/retrieve", json=retrieve_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["has_relevant_evidence"] is False
    assert len(data["results"]) == 0
