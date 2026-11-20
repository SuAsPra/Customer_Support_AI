from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator

class SessionCreateRequest(BaseModel):
    mode: Literal["simulator", "manual", "replay"] = Field(
        ..., description="Interaction mode: simulator, manual, or replay"
    )
    product_context: str = Field(..., min_length=1, description="Product or service context (e.g. ApexGear E-Commerce)")
    scenario: str = Field(..., min_length=1, description="Customer scenario / problem description")
    persona: Optional[str] = Field(None, description="Customer persona for simulator mode (e.g. impatient, confused, angry)")
    emotional_progression: Optional[str] = Field(None, description="Intended emotional progression (e.g. frustrated -> neutral -> satisfied)")

    @model_validator(mode="after")
    def validate_mode_requirements(self):
        if self.mode == "simulator" and not self.persona:
            # Default persona if omitted in simulator mode
            self.persona = "impatient"
        return self

class ReplayTranscriptResponse(BaseModel):
    id: int
    session_id: str
    filename: str
    file_format: str
    message_count: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SessionResponse(BaseModel):
    id: str
    mode: str
    product_context: str
    scenario: str
    persona: Optional[str] = None
    emotional_progression: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    transcript: Optional[ReplayTranscriptResponse] = None

    model_config = ConfigDict(from_attributes=True)
