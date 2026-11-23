from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.db import models  # noqa: F401 ensure models registered
from app.api import sessions, kb

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Customer Support Coaching Assistant", version="0.1.0 (Milestone 1)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions.router)
app.include_router(kb.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "milestone": 1}
