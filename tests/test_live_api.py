"""
Live API Endpoints Testing Script via real Uvicorn HTTP server and HTTPX client.
Tests:
1. GET  /api/health
2. POST /api/kb/documents (upload sample PDF)
3. GET  /api/kb/documents (list documents)
4. GET  /api/kb/documents/{id} (get document details and chunks)
5. POST /api/kb/retrieve (semantic query retrieval with grounding)
6. Error handling: 422 for empty query, 404 for nonexistent document
7. Session endpoints: POST /api/sessions, GET /api/sessions/{id}
"""

import os
import sys
import time
import json
import threading
import httpx
import uvicorn
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force offline mode
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from app.main import app
from app.core.config import get_settings

TEST_PORT = 8008
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"

def run_live_api_tests():
    print("=" * 80)
    print("STARTING LIVE FASTAPI SERVER & ENDPOINT VERIFICATION")
    print(f"Target: {BASE_URL}")
    print("=" * 80)

    # Start Uvicorn in background thread
    config = uvicorn.Config(app=app, host="127.0.0.1", port=TEST_PORT, log_level="warning")
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    # Wait for server to become responsive
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)
    max_retries = 10
    ready = False
    for i in range(max_retries):
        try:
            r = client.get("/api/health")
            if r.status_code == 200:
                ready = True
                print(f"Server is UP and responsive after {i+1} attempt(s)!\n")
                break
        except Exception:
            time.sleep(0.5)

    if not ready:
        print("ERROR: Server failed to start within timeout.")
        server.should_exit = True
        return False

    results_summary = {}

    try:
        # TEST 1: GET /api/health
        print("--- [1] GET /api/health ---")
        res_health = client.get("/api/health")
        print(f"Status: {res_health.status_code}")
        print(f"Response: {json.dumps(res_health.json(), indent=2)}")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"
        results_summary["GET /api/health"] = "PASSED (200)"

        # TEST 2: POST /api/kb/documents
        print("\n--- [2] POST /api/kb/documents ---")
        sample_pdf_path = PROJECT_ROOT / "data" / "sample_docs" / "returns_and_refunds_policy.pdf"
        with open(sample_pdf_path, "rb") as f:
            pdf_bytes = f.read()

        files = {"file": ("returns_and_refunds_policy.pdf", pdf_bytes, "application/pdf")}
        data = {"doc_type": "pdf", "product_domain": "ecommerce"}
        res_upload = client.post("/api/kb/documents", files=files, data=data)
        print(f"Status: {res_upload.status_code}")
        upload_json = res_upload.json()
        print(f"Response (summary): id={upload_json.get('id')}, filename={upload_json.get('filename')}, status={upload_json.get('status')}, chunks={upload_json.get('chunk_count')}")
        assert res_upload.status_code in (200, 201)
        doc_id = upload_json["id"]
        results_summary["POST /api/kb/documents"] = f"PASSED ({res_upload.status_code})"

        # TEST 3: GET /api/kb/documents
        print("\n--- [3] GET /api/kb/documents ---")
        res_list = client.get("/api/kb/documents")
        print(f"Status: {res_list.status_code}")
        docs = res_list.json()
        print(f"Found {len(docs)} document(s) in KB:")
        for d in docs[:3]:
            print(f"  - ID: {d['id']}, Name: {d['filename']}, Status: {d['status']}, Chunks: {d['chunk_count']}")
        assert res_list.status_code == 200
        assert len(docs) >= 1
        results_summary["GET /api/kb/documents"] = "PASSED (200)"

        # TEST 4: GET /api/kb/documents/{id}
        print(f"\n--- [4] GET /api/kb/documents/{doc_id} ---")
        res_detail = client.get(f"/api/kb/documents/{doc_id}")
        print(f"Status: {res_detail.status_code}")
        detail = res_detail.json()
        print(f"Document: {detail['filename']} (Hash: {detail['file_hash'][:16]}...)")
        print(f"Total Chunks: {len(detail['chunks'])}")
        if detail['chunks']:
            first_chunk = detail['chunks'][0]
            print(f"Sample Chunk 0: Section='{first_chunk['section']}', Tokens={first_chunk['token_count']}")
            print(f"Preview: {first_chunk['text_preview']}")
        assert res_detail.status_code == 200
        assert len(detail["chunks"]) == detail["chunk_count"]
        results_summary["GET /api/kb/documents/{id}"] = "PASSED (200)"

        # TEST 5: POST /api/kb/retrieve
        print("\n--- [5] POST /api/kb/retrieve ---")
        query_payload = {
            "query": "How many days do I have to return an item and what condition must it be in?",
            "product_domain": "ecommerce",
            "top_k": 3,
            "score_threshold": 0.35
        }
        res_retrieve = client.post("/api/kb/retrieve", json=query_payload)
        print(f"Status: {res_retrieve.status_code}")
        retr_json = res_retrieve.json()
        print(f"Query: '{retr_json['query']}'")
        print(f"Has Evidence: {retr_json['has_relevant_evidence']}, Total: {retr_json['total_results']}")
        for r in retr_json["results"]:
            print(f"  Rank {r['rank']}: Score={r['relevance_score']:.4f} | [{r['section']}] ({r['source_filename']} p.{r['page_number']})")
            print(f"    Text: {r['text'][:100]}...")
        assert res_retrieve.status_code == 200
        assert retr_json["has_relevant_evidence"] is True
        assert len(retr_json["results"]) > 0
        results_summary["POST /api/kb/retrieve"] = "PASSED (200)"

        # TEST 6: Request Validation & Error Handling
        print("\n--- [6] Error Handling & Validation ---")
        # Empty query validation
        empty_res = client.post("/api/kb/retrieve", json={"query": ""})
        print(f"Empty query validation: Status={empty_res.status_code} (Expected 422)")
        assert empty_res.status_code == 422

        # 404 for non-existent document
        not_found_res = client.get("/api/kb/documents/999999")
        print(f"Non-existent document: Status={not_found_res.status_code} (Expected 404)")
        assert not_found_res.status_code == 404
        results_summary["Error Handling (422, 404)"] = "PASSED (422, 404)"

        # TEST 7: Session Configuration Endpoints
        print("\n--- [7] POST /api/sessions & GET /api/sessions/{id} ---")
        session_payload = {
            "mode": "simulator",
            "product_context": "ApexGear E-Commerce",
            "scenario": "Customer received damaged product and asks for refund",
            "persona": "impatient",
            "emotional_progression": "frustrated -> neutral -> satisfied"
        }
        res_sess = client.post("/api/sessions", json=session_payload)
        print(f"Create Session Status: {res_sess.status_code}")
        sess_data = res_sess.json()
        sess_id = sess_data["id"]
        print(f"Created Session ID: {sess_id}, Mode: {sess_data['mode']}, Status: {sess_data['status']}")
        assert res_sess.status_code == 201

        res_sess_get = client.get(f"/api/sessions/{sess_id}")
        print(f"Get Session Status: {res_sess_get.status_code}")
        assert res_sess_get.status_code == 200
        assert res_sess_get.json()["id"] == sess_id
        results_summary["Session Configuration APIs"] = "PASSED (201, 200)"

        print("\n" + "=" * 80)
        print("ALL LIVE API TESTS PASSED SUCCESSFULLY!")
        print("=" * 80)
        for ep, status_str in results_summary.items():
            print(f"  ✓ {ep:<35} : {status_str}")
        print("=" * 80)
        return True

    finally:
        client.close()
        server.should_exit = True

if __name__ == "__main__":
    success = run_live_api_tests()
    sys.exit(0 if success else 1)
