"""PhysioWave — Pydantic Models (API schemas)."""

from datetime import datetime

from pydantic import BaseModel, Field


# ─── Patient ──────────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    risk_factors: list[str] = []
    notes: str | None = None

class PatientResponse(BaseModel):
    id: str
    age: int | None = None
    gender: str | None = None
    risk_factors: list[str] = []
    notes: str | None = None
    created_at: str
    session_count: int = 0


# ─── Intake Form ──────────────────────────────────────────────────────

class IntakeForm(BaseModel):
    patient_id: str | None = None
    age: int | None = None
    gender: str | None = None
    diagnosis: str
    pain_scale: int | None = Field(None, ge=0, le=10)
    condition_phase: str | None = None  # acute / subacute / chronic
    body_area: str | None = None
    symptoms: str | None = None
    risk_factors: list[str] = []
    additional_notes: str | None = None


# ─── AI Suggestion ────────────────────────────────────────────────────

class SuggestionResponse(BaseModel):
    id: str
    suggestion: str
    source_chunks: list[dict] = []
    is_safe: bool
    warning_message: str | None = None
    blocked_protocols: list[str] = []
    query: str


# ─── Safety Check ─────────────────────────────────────────────────────

class SafetyCheckRequest(BaseModel):
    risk_factors: list[str]
    suggested_protocol: str | None = None

class SafetyCheckResponse(BaseModel):
    is_safe: bool
    blocked_protocols: list[str] = []
    conflicts: list[dict] = []
    warning_message: str | None = None


# ─── Session ──────────────────────────────────────────────────────────

class SessionCreate(BaseModel):
    patient_id: str
    symptoms: str | None = None
    vitals: dict | None = None
    diagnosis: str | None = None
    therapy_used: str | None = None
    machine_settings: dict | None = None
    duration_minutes: int | None = None
    pain_score_before: int | None = Field(None, ge=0, le=10)
    pain_score_after: int | None = Field(None, ge=0, le=10)
    notes: str | None = None

class SessionResponse(BaseModel):
    id: str
    patient_id: str
    symptoms: str | None = None
    diagnosis: str | None = None
    therapy_used: str | None = None
    duration_minutes: int | None = None
    pain_score_before: int | None = None
    pain_score_after: int | None = None
    notes: str | None = None
    status: str = "active"
    created_at: str


# ─── RAG ──────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    document_type: str | None = None

class SearchResultItem(BaseModel):
    content: str
    score: float
    source_file: str
    page_number: int | None = None
    document_type: str | None = None


# ─── Health ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    ollama_running: bool
    llm_model_ready: bool
    embedding_model_ready: bool
    vector_store_count: int
    database_ready: bool
