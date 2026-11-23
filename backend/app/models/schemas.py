from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Literal, Any
from datetime import datetime


Mode = Literal["simulator", "manual", "replay"]


class SessionCreate(BaseModel):
    mode: Mode
    product_context: str = Field(min_length=1)
    scenario: str = Field(min_length=1)
    persona: str | None = None
    emotional_progression: str | None = None
    transcript: Any | None = None  # for replay: JSON list or raw text

    @field_validator("product_context", "scenario", mode="before")
    @classmethod
    def strip_required_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("persona", mode="before")
    @classmethod
    def strip_persona(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_by_mode(self):
        if self.mode == "simulator" and not self.persona:
            raise ValueError("persona is required for simulator mode")
        if self.mode == "replay" and self.transcript is None:
            raise ValueError("transcript is required for replay mode")
        return self


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    mode: str
    product_context: str
    scenario: str
    persona: str | None = None
    emotional_progression: str | None = None
    status: str
    transcript_meta: dict | None = None
    created_at: datetime
    ended_at: datetime | None = None

class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    session_id: str
    sender: str
    text: str
    turn_number: int
    timestamp: datetime

class KBDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    error: str | None = None
    upload_time: datetime

class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1)
    session_id: str | None = None

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, value):
        return value.strip() if isinstance(value, str) else value


class RetrieveResult(BaseModel):
    chunk_id: str
    document_id: str
    source: str
    section: str | None = None
    text: str
    score: float


class RetrieveResponse(BaseModel):
    query: str
    top_k: int
    results: list[RetrieveResult]
    count: int
