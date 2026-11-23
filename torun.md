 Prerequisites
 Python 3.11 or 3.12 and pip (avoid Python 3.14 with the currently pinned dependencies)
Internet access on first run (to download the local embedding model all-MiniLM-L6-v2 if not cached)
Project root: C:\Customer_Service_AI (your .env is already configured)
2. Open a terminal in the project root
cd C:\Customer_Service_AI
3. Create and activate a virtual environment (recommended)
Windows (PowerShell; Python 3.12):

py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
macOS/Linux:

python3.12 -m venv .venv
source .venv/bin/activate
4. Install dependencies
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
First install may take a few minutes (includes ML/embedding dependencies).
On Windows, Python 3.12 may require Microsoft C++ Build Tools to compile chroma-hnswlib; Python 3.11 has a prebuilt wheel for the pinned version.

5. Verify environment config
Ensure .env exists in the repo root (you already have it configured with Gemini and SQLite).
Default Milestone 1 paths/DB: DATABASE_URL=sqlite:///./data/app.db, CHROMA_PERSIST_DIR=./data/chroma, uploads in ./data/uploads (created automatically).
6. Start the backend server
Run from the repo root:

python -m uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000
API: http://localhost:8000
Swagger UI (interactive docs): http://localhost:8000/docs
Health check: http://localhost:8000/api/health
7. Use the program (Milestone 1 demo via Swagger/Postman)
A. Create sessions (all 3 modes) — POST /api/sessions
Simulator (requires persona):
{
  "mode": "simulator",
  "product_context": "ShopNest e-commerce support",
  "scenario": "Customer charged twice for subscription",
  "persona": "impatient",
  "emotional_progression": "frustrated -> angry if unresolved -> relieved if refund confirmed"
}
Manual:
{
  "mode": "manual",
  "product_context": "ShopNest e-commerce support",
  "scenario": "Customer asking about missing delivery"
}
Replay (requires transcript):
{
  "mode": "replay",
  "product_context": "ShopNest e-commerce support",
  "scenario": "Refund delay follow-up",
  "transcript": [
    {"sender": "customer", "text": "I returned my order 10 days ago and still no refund."},
    {"sender": "agent", "text": "I'm sorry about the delay. Can I have your order ID?"}
  ]
}
Verify: GET /api/sessions and GET /api/sessions/{session_id}
B. Upload and index knowledge base docs — POST /api/kb/documents
In Swagger, use multipart upload (file) for each file in sample_kb/shopnest/:
faq.md, refund_policy.md, shipping_and_delivery.md, troubleshooting.md
Check status/chunk counts: GET /api/kb/documents (should show status: indexed)
C. Retrieve relevant information — POST /api/kb/retrieve
{
  "query": "I was charged twice for my subscription. What should I do?",
  "top_k": 5
}
Returns ranked chunks with text, source, section, and score
Test more queries from sample_kb/retrieval_test_set.json
8. (Optional) Generate actual retrieval test results
python backend/scripts/evaluate_retrieval.py
Updates docs/retrieval_test_results.md with summary and per-question results.