"""PhysioWave — Smart Treatment Advisor Router.

Implements the three-pass Multi-Agentic pipeline via REST API:
- POST /advisor/suggest — streaming AI suggestion from intake form
- POST /advisor/check-safety — real-time contraindication check
"""

import json
import uuid

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.ai.suggestion import generate_suggestion, generate_suggestion_stream
from backend.models.schemas import (
    IntakeForm,
    SafetyCheckRequest,
    SafetyCheckResponse,
    SuggestionResponse,
)
from backend.safety.contraindications import get_blocked_protocols, get_conflict_details
from backend.safety.interceptor import safety_interceptor

router = APIRouter(prefix="/advisor", tags=["Smart Treatment Advisor"])


@router.post("/suggest", response_model=SuggestionResponse)
async def suggest_treatment(intake: IntakeForm):
    """Generate an AI therapy suggestion (non-streaming).

    Executes the full three-pass pipeline:
    1. Extract & analyze intake form
    2. Retrieve clinical context from vector store
    3. Generate suggestion via Gemma 3 4B + safety validation
    """
    result = generate_suggestion(
        age=intake.age,
        gender=intake.gender,
        diagnosis=intake.diagnosis,
        pain_scale=intake.pain_scale,
        condition_phase=intake.condition_phase,
        body_area=intake.body_area,
        symptoms=intake.symptoms,
        risk_factors=set(intake.risk_factors),
        additional_notes=intake.additional_notes,
    )

    return SuggestionResponse(
        id=result.id,
        suggestion=result.suggestion,
        source_chunks=result.source_chunks,
        is_safe=result.safety.is_safe,
        warning_message=result.safety.warning_message,
        blocked_protocols=[
            c.protocol for c in result.safety.conflicts
        ],
        query=result.query,
    )


@router.post("/suggest/stream")
async def suggest_treatment_stream(intake: IntakeForm):
    """Generate an AI therapy suggestion (streaming via SSE).

    Streams tokens as Server-Sent Events for real-time UI display.
    """
    def event_stream():
        try:
            for token in generate_suggestion_stream(
                age=intake.age,
                gender=intake.gender,
                diagnosis=intake.diagnosis,
                pain_scale=intake.pain_scale,
                condition_phase=intake.condition_phase,
                body_area=intake.body_area,
                symptoms=intake.symptoms,
                risk_factors=set(intake.risk_factors),
                additional_notes=intake.additional_notes,
            ):
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/check-safety", response_model=SafetyCheckResponse)
async def check_safety(request: SafetyCheckRequest):
    """Check if a therapy protocol is safe given patient risk factors."""
    factors = set(request.risk_factors)
    blocked = get_blocked_protocols(factors)

    conflicts = []
    if request.suggested_protocol:
        details = get_conflict_details(request.suggested_protocol, factors)
        for factor, protocols in details.items():
            conflicts.append({
                "risk_factor": factor,
                "blocked_protocols": list(protocols),
            })

    is_safe = not blocked if not request.suggested_protocol else len(conflicts) == 0

    result = safety_interceptor.validate(
        suggestion=request.suggested_protocol or "",
        risk_factors=factors,
    )

    return SafetyCheckResponse(
        is_safe=result.is_safe,
        blocked_protocols=list(blocked),
        conflicts=conflicts,
        warning_message=result.warning_message,
    )
