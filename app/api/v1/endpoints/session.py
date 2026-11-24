import uuid
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.session import Session as SessionModel, ReplayTranscript
from app.schemas.session import SessionCreateRequest, SessionResponse, ReplayTranscriptResponse

logger = logging.getLogger("support_coach.api.session")

router = APIRouter(prefix="/sessions", tags=["Session Configuration"])

@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support coaching session"
)
def create_session(
    request: SessionCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Creates and configures a coaching session:
    - Supports Simulator, Manual, or Replay modes
    - Validates mode-specific context (persona, emotional progression)
    - Generates unique session_id (e.g., sess-xxxxxxxx)
    """
    session_id = f"sess-{uuid.uuid4().hex[:12]}"
    new_session = SessionModel(
        id=session_id,
        mode=request.mode,
        product_context=request.product_context,
        scenario=request.scenario,
        persona=request.persona,
        emotional_progression=request.emotional_progression,
        status="created"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info("Created session '%s' (mode: %s)", session_id, request.mode)
    return new_session

@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get coaching session details by ID"
)
def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves session configuration and status by session_id."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found."
        )
    return session

@router.get(
    "",
    response_model=List[SessionResponse],
    summary="List all coaching sessions"
)
def list_sessions(
    mode: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists coaching sessions with optional filtering by mode and status."""
    query = db.query(SessionModel)
    if mode:
        query = query.filter(SessionModel.mode == mode)
    if status_filter:
        query = query.filter(SessionModel.status == status_filter)
    return query.order_by(SessionModel.created_at.desc()).all()

@router.post(
    "/{session_id}/transcript",
    response_model=ReplayTranscriptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload replay transcript for Replay mode"
)
def upload_replay_transcript(
    session_id: str,
    file: UploadFile = File(..., description="Transcript file (TXT or JSON)"),
    db: Session = Depends(get_db)
):
    """Uploads a customer-agent dialogue transcript for Replay mode playback."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session with ID '{session_id}' not found."
        )
    if session.mode != "replay":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session '{session_id}' has mode '{session.mode}'. Transcripts can only be uploaded for 'replay' sessions."
        )

    try:
        raw_bytes = file.file.read()
        raw_content = raw_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to read transcript: {str(e)}")

    # Count messages (JSON array or line-by-line format)
    message_count = 0
    filename_lower = (file.filename or "").lower()
    file_format = "json" if filename_lower.endswith(".json") else "txt"

    if file_format == "json":
        try:
            data = json.loads(raw_content)
            message_count = len(data) if isinstance(data, list) else len(data.get("messages", []))
        except Exception:
            message_count = len([l for l in raw_content.splitlines() if l.strip()])
    else:
        message_count = len([l for l in raw_content.splitlines() if l.strip()])

    # Replace existing transcript if present
    existing = db.query(ReplayTranscript).filter(ReplayTranscript.session_id == session_id).first()
    if existing:
        existing.filename = file.filename or "transcript.txt"
        existing.file_format = file_format
        existing.raw_content = raw_content
        existing.message_count = message_count
        db.commit()
        db.refresh(existing)
        return existing

    transcript = ReplayTranscript(
        session_id=session_id,
        filename=file.filename or "transcript.txt",
        file_format=file_format,
        raw_content=raw_content,
        message_count=message_count
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)
    return transcript
