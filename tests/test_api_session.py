import pytest

def test_create_simulator_session(client):
    payload = {
        "mode": "simulator",
        "product_context": "ApexGear E-Commerce",
        "scenario": "Customer received defective headphones and demands refund",
        "persona": "impatient",
        "emotional_progression": "frustrated -> neutral"
    }
    response = client.post("/api/sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"].startswith("sess-")
    assert data["mode"] == "simulator"
    assert data["status"] == "created"
    assert data["persona"] == "impatient"

def test_create_manual_session(client):
    payload = {
        "mode": "manual",
        "product_context": "ApexTelecom Mobile Plans",
        "scenario": "Customer asking about international roaming"
    }
    response = client.post("/api/sessions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mode"] == "manual"

def test_get_session(client):
    payload = {
        "mode": "replay",
        "product_context": "ApexGear Tech Support",
        "scenario": "Customer audio crackling issue"
    }
    create_res = client.post("/api/sessions", json=payload)
    sess_id = create_res.json()["id"]

    get_res = client.get(f"/api/sessions/{sess_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == sess_id
    assert get_res.json()["mode"] == "replay"

def test_upload_replay_transcript(client):
    # 1. Create replay session
    create_res = client.post("/api/sessions", json={
        "mode": "replay",
        "product_context": "ApexGear Returns",
        "scenario": "Past return conversation"
    })
    sess_id = create_res.json()["id"]

    # 2. Upload transcript
    transcript_text = "Customer: Hi, I need to return an item.\nAgent: Hello, I can help with that."
    res = client.post(
        f"/api/sessions/{sess_id}/transcript",
        files={"file": ("chat.txt", transcript_text.encode("utf-8"), "text/plain")}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["session_id"] == sess_id
    assert data["message_count"] == 2
    assert data["file_format"] == "txt"
