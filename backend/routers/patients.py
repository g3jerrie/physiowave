"""PhysioWave — Patient Records Router."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from backend.core.database import get_db
from backend.models.schemas import PatientCreate, PatientResponse

router = APIRouter(prefix="/patients", tags=["Patient Records"])


@router.get("", response_model=list[PatientResponse])
async def list_patients():
    """List all patients."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT p.*, COUNT(s.id) as session_count
            FROM patients p
            LEFT JOIN sessions s ON s.patient_id = p.id
            GROUP BY p.id
            ORDER BY p.created_at DESC
            """
        )
        rows = await cursor.fetchall()
        return [
            PatientResponse(
                id=row["id"],
                age=row["age"],
                gender=row["gender"],
                risk_factors=json.loads(row["risk_factors"] or "[]"),
                notes=row["notes"],
                created_at=row["created_at"],
                session_count=row["session_count"],
            )
            for row in rows
        ]
    finally:
        await db.close()


@router.post("", response_model=PatientResponse, status_code=201)
async def create_patient(patient: PatientCreate):
    """Create a new patient record."""
    patient_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO patients (id, age, gender, risk_factors, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                patient_id,
                patient.age,
                patient.gender,
                json.dumps(patient.risk_factors),
                patient.notes,
                now,
                now,
            ),
        )
        await db.commit()

        return PatientResponse(
            id=patient_id,
            age=patient.age,
            gender=patient.gender,
            risk_factors=patient.risk_factors,
            notes=patient.notes,
            created_at=now,
            session_count=0,
        )
    finally:
        await db.close()


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get a single patient by ID."""
    db = await get_db()
    try:
        cursor = await db.execute(
            """
            SELECT p.*, COUNT(s.id) as session_count
            FROM patients p
            LEFT JOIN sessions s ON s.patient_id = p.id
            WHERE p.id = ?
            GROUP BY p.id
            """,
            (patient_id,),
        )
        row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Patient not found")

        return PatientResponse(
            id=row["id"],
            age=row["age"],
            gender=row["gender"],
            risk_factors=json.loads(row["risk_factors"] or "[]"),
            notes=row["notes"],
            created_at=row["created_at"],
            session_count=row["session_count"],
        )
    finally:
        await db.close()


@router.delete("/{patient_id}", status_code=204)
async def delete_patient(patient_id: str):
    """Delete a patient and all associated records."""
    db = await get_db()
    try:
        cursor = await db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        await db.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Patient not found")
    finally:
        await db.close()
