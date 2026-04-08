"""PhysioWave — Session Management Router."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.core.database import get_db
from backend.models.schemas import SessionCreate, SessionResponse

router = APIRouter(prefix="/sessions", tags=["Treatment Sessions"])


@router.get("", response_model=list[SessionResponse])
async def list_sessions(patient_id: str | None = None):
    """List sessions, optionally filtered by patient."""
    db = await get_db()
    try:
        if patient_id:
            cursor = await db.execute(
                "SELECT * FROM sessions WHERE patient_id = ? ORDER BY created_at DESC",
                (patient_id,),
            )
        else:
            cursor = await db.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC LIMIT 50"
            )
        rows = await cursor.fetchall()
        return [_row_to_response(row) for row in rows]
    finally:
        await db.close()


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(session: SessionCreate):
    """Create a new therapy session."""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO sessions (
                id, patient_id, symptoms, vitals, diagnosis,
                therapy_used, machine_settings, duration_minutes,
                pain_score_before, pain_score_after, notes,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session.patient_id,
                session.symptoms,
                json.dumps(session.vitals) if session.vitals else None,
                session.diagnosis,
                session.therapy_used,
                json.dumps(session.machine_settings) if session.machine_settings else None,
                session.duration_minutes,
                session.pain_score_before,
                session.pain_score_after,
                session.notes,
                "active",
                now,
                now,
            ),
        )
        await db.commit()

        return SessionResponse(
            id=session_id,
            patient_id=session.patient_id,
            symptoms=session.symptoms,
            diagnosis=session.diagnosis,
            therapy_used=session.therapy_used,
            duration_minutes=session.duration_minutes,
            pain_score_before=session.pain_score_before,
            pain_score_after=session.pain_score_after,
            notes=session.notes,
            status="active",
            created_at=now,
        )
    finally:
        await db.close()


@router.put("/{session_id}/complete", response_model=SessionResponse)
async def complete_session(
    session_id: str,
    pain_score_after: int | None = None,
    notes: str | None = None,
):
    """Mark a session as completed."""
    now = datetime.now(timezone.utc).isoformat()
    db = await get_db()
    try:
        updates = ["status = 'completed'", "updated_at = ?"]
        params: list = [now]

        if pain_score_after is not None:
            updates.append("pain_score_after = ?")
            params.append(pain_score_after)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        params.append(session_id)

        await db.execute(
            f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        await db.commit()

        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        return _row_to_response(row)
    finally:
        await db.close()


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a single session by ID."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")
        return _row_to_response(row)
    finally:
        await db.close()


def _row_to_response(row) -> SessionResponse:
    return SessionResponse(
        id=row["id"],
        patient_id=row["patient_id"],
        symptoms=row["symptoms"],
        diagnosis=row["diagnosis"],
        therapy_used=row["therapy_used"],
        duration_minutes=row["duration_minutes"],
        pain_score_before=row["pain_score_before"],
        pain_score_after=row["pain_score_after"],
        notes=row["notes"],
        status=row["status"],
        created_at=row["created_at"],
    )
