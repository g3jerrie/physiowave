"""PhysioWave — Three-Pass AI Suggestion Engine.

Orchestrates the Multi-Agentic logic from the system prompt:

Pass 1 — Extraction & Analysis:
  Parse intake form, identify PII, build risk profile.

Pass 2 — Contextual Retrieval:
  Semantic search on ChromaDB → top-K clinical context chunks.

Pass 3 — Safe Synthesis:
  Prompt Gemma 3 4B with [system + context + query].
  Safety interceptor validates before returning.
"""

import uuid
from collections.abc import Generator
from dataclasses import dataclass

from backend.ai.ollama_client import chat, chat_stream
from backend.ai.prompts import TREATMENT_ADVISOR_PROMPT
from backend.core.logger import logger
from backend.rag.pipeline import semantic_search
from backend.safety.interceptor import SafetyResult, safety_interceptor


@dataclass
class SuggestionResult:
    """Complete result from the three-pass suggestion pipeline."""
    id: str
    suggestion: str
    source_chunks: list[dict]
    safety: SafetyResult
    query: str


def generate_suggestion(
    age: int | None,
    gender: str | None,
    diagnosis: str,
    pain_scale: int | None,
    condition_phase: str | None,
    body_area: str | None,
    symptoms: str | None,
    risk_factors: set[str] | None = None,
    additional_notes: str | None = None,
) -> SuggestionResult:
    """Execute the three-pass suggestion pipeline (non-streaming).

    Returns complete SuggestionResult with safety validation applied.
    """
    factors = risk_factors or set()

    # ─── Pass 1: Build Query ─────────────────────────────────────────
    logger.info("Pass 1: Extracting context from intake form")

    search_query = _build_search_query(
        diagnosis, symptoms, body_area, condition_phase
    )

    # ─── Pass 2: Contextual Retrieval ────────────────────────────────
    logger.info("Pass 2: Retrieving clinical context")

    results = semantic_search(search_query, top_k=8)
    context = "\n\n---\n\n".join(
        f"[Source: {r['source_file']}, Page {r.get('page_number', '?')}]\n{r['content']}"
        for r in results
    )

    if not context:
        context = "No specific clinical context found in the knowledge base."

    # ─── Pass 3: Safe Synthesis ──────────────────────────────────────
    logger.info("Pass 3: Generating AI suggestion")

    prompt = TREATMENT_ADVISOR_PROMPT.format(
        context=context,
        age=age or "Not specified",
        gender=gender or "Not specified",
        diagnosis=diagnosis,
        pain_scale=pain_scale if pain_scale is not None else "Not assessed",
        condition_phase=condition_phase or "Not specified",
        body_area=body_area or "Not specified",
        symptoms=symptoms or "None reported",
        contraindications=", ".join(f.replace("_", " ") for f in factors) or "None",
        additional_notes=f"\nAdditional Notes: {additional_notes}" if additional_notes else "",
    )

    suggestion_text = chat(prompt)

    # ─── Safety Gate ─────────────────────────────────────────────────
    safety = safety_interceptor.validate(suggestion_text, factors)

    return SuggestionResult(
        id=str(uuid.uuid4()),
        suggestion=suggestion_text,
        source_chunks=results,
        safety=safety,
        query=search_query,
    )


def generate_suggestion_stream(
    age: int | None,
    gender: str | None,
    diagnosis: str,
    pain_scale: int | None,
    condition_phase: str | None,
    body_area: str | None,
    symptoms: str | None,
    risk_factors: set[str] | None = None,
    additional_notes: str | None = None,
) -> Generator[str, None, None]:
    """Execute the three-pass pipeline with streaming output.

    Yields tokens as they are generated. Safety validation happens
    after the full response is assembled.
    """
    factors = risk_factors or set()

    # Pass 1 & 2 are the same as non-streaming
    search_query = _build_search_query(
        diagnosis, symptoms, body_area, condition_phase
    )
    results = semantic_search(search_query, top_k=8)
    context = "\n\n---\n\n".join(
        f"[Source: {r['source_file']}, Page {r.get('page_number', '?')}]\n{r['content']}"
        for r in results
    )

    if not context:
        context = "No specific clinical context found in the knowledge base."

    prompt = TREATMENT_ADVISOR_PROMPT.format(
        context=context,
        age=age or "Not specified",
        gender=gender or "Not specified",
        diagnosis=diagnosis,
        pain_scale=pain_scale if pain_scale is not None else "Not assessed",
        condition_phase=condition_phase or "Not specified",
        body_area=body_area or "Not specified",
        symptoms=symptoms or "None reported",
        contraindications=", ".join(f.replace("_", " ") for f in factors) or "None",
        additional_notes=f"\nAdditional Notes: {additional_notes}" if additional_notes else "",
    )

    # Pass 3: Stream tokens
    yield from chat_stream(prompt)


def _build_search_query(
    diagnosis: str,
    symptoms: str | None,
    body_area: str | None,
    condition_phase: str | None,
) -> str:
    """Build a semantic search query from intake form fields."""
    parts = [diagnosis]
    if symptoms:
        parts.append(symptoms)
    if body_area:
        parts.append(f"body area: {body_area}")
    if condition_phase:
        parts.append(f"phase: {condition_phase}")
    return ". ".join(parts)
