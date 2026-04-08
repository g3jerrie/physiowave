"""PhysioWave — Health Check Router."""

from fastapi import APIRouter

from backend.ai.ollama_client import check_ollama_status
from backend.models.schemas import HealthResponse
from backend.rag.vector_store import get_document_count

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health: Ollama, models, database, vector store."""
    ollama_status = check_ollama_status()

    try:
        count = get_document_count()
        db_ready = True
    except Exception:
        count = 0
        db_ready = False

    return HealthResponse(
        status="ok" if ollama_status.get("ollama_running") else "degraded",
        ollama_running=ollama_status.get("ollama_running", False),
        llm_model_ready=ollama_status.get("llm_model_ready", False),
        embedding_model_ready=ollama_status.get("embedding_model_ready", False),
        vector_store_count=count,
        database_ready=db_ready,
    )
