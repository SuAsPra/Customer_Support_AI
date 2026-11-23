import json
from sqlalchemy.orm import Session as DBSession
from app.db import models
from app.models.schemas import SessionCreate


def _parse_transcript(transcript) -> tuple[list[dict], dict]:
    items = []
    if transcript is None:
        return items, {"count": 0}
    if isinstance(transcript, str):
        s = transcript.strip()
        # try JSON first
        try:
            data = json.loads(s)
            transcript = data
        except Exception:
            # simple line format: "customer: ..." or "agent: ..."
            lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
            parsed = []
            for ln in lines:
                if ":" in ln:
                    sender, text = ln.split(":", 1)
                    sender = sender.strip().lower()
                    if sender not in {"customer", "agent", "system"}:
                        sender = "customer"
                    parsed.append({"sender": sender, "text": text.strip()})
                else:
                    parsed.append({"sender": "customer", "text": ln})
            transcript = parsed
    if isinstance(transcript, dict) and "messages" in transcript:
        transcript = transcript["messages"]
    if isinstance(transcript, list):
        for it in transcript:
            if isinstance(it, dict):
                sender = str(it.get("sender", "customer")).lower()
                text = str(it.get("text", "")).strip()
                if text:
                    items.append({"sender": sender if sender in {"customer", "agent", "system"} else "customer", "text": text})
            elif isinstance(it, str) and it.strip():
                items.append({"sender": "customer", "text": it.strip()})
    return items, {"count": len(items), "format": "json"}


def create_session(db: DBSession, payload: SessionCreate) -> models.Session:
    transcript_meta = None
    transcript_items = []
    if payload.mode == "replay":
        transcript_items, transcript_meta = _parse_transcript(payload.transcript)
        if not transcript_items:
            raise ValueError("transcript must contain at least one non-empty message")

    sess = models.Session(
        mode=payload.mode,
        product_context=payload.product_context.strip(),
        scenario=payload.scenario.strip(),
        persona=payload.persona.strip() if payload.persona else None,
        emotional_progression=payload.emotional_progression,
        status="created",
        transcript_meta=transcript_meta,
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    # store replay messages if provided
    if transcript_items:
        for idx, it in enumerate(transcript_items, start=1):
            msg = models.Message(session_id=sess.id, sender=it["sender"], text=it["text"], turn_number=idx)
            db.add(msg)
        db.commit()
    return sess


def get_session(db: DBSession, session_id: str) -> models.Session | None:
    return db.query(models.Session).filter(models.Session.id == session_id).first()


def list_sessions(db: DBSession) -> list[models.Session]:
    return db.query(models.Session).order_by(models.Session.created_at.desc()).all()
