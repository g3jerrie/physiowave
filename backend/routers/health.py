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

from pydantic import BaseModel
from backend.core.config import settings

class ConfigUpdate(BaseModel):
    llm_model: str
    vision_model: str

@router.get("/config")
async def get_config():
    return {
        "llm_model": settings.llm_model,
        "vision_model": settings.vision_model,
        "embedding_model": settings.embedding_model,
    }

@router.post("/config")
async def update_config(data: ConfigUpdate):
    settings.llm_model = data.llm_model
    settings.vision_model = data.vision_model
    
    # Attempt to persist to .env file if it exists
    try:
        import os
        env_path = "./backend/.env"
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()
            with open(env_path, "w") as f:
                found_llm = False
                found_vision = False
                for line in lines:
                    if line.startswith("LLM_MODEL="):
                        f.write(f"LLM_MODEL={data.llm_model}\n")
                        found_llm = True
                    elif line.startswith("VISION_MODEL="):
                        f.write(f"VISION_MODEL={data.vision_model}\n")
                        found_vision = True
                    else:
                        f.write(line)
                if not found_llm:
                    f.write(f"LLM_MODEL={data.llm_model}\n")
                if not found_vision:
                    f.write(f"VISION_MODEL={data.vision_model}\n")
    except Exception:
        pass # fallback to in-memory updates
        
    return {"status": "updated"}
