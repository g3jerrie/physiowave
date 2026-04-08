"""PhysioWave — Ollama LLM Client.

HIPAA Compliance Note: All inference runs 100% on-device via Ollama.
No data is transmitted to any external server.
"""

from collections.abc import Generator

import ollama

from backend.core.config import settings
from backend.core.logger import logger
from backend.ai.prompts import CLINICAL_SYSTEM_PROMPT


def chat_stream(
    prompt: str,
    system_prompt: str | None = None,
) -> Generator[str, None, None]:
    """Stream LLM response token-by-token.

    Yields individual tokens as they are generated.
    Uses Ollama's /api/chat endpoint with streaming.
    """
    sys_prompt = system_prompt or CLINICAL_SYSTEM_PROMPT

    try:
        stream = ollama.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=True,
            options={
                "temperature": settings.llm_temperature,
                "top_k": settings.llm_top_k,
                "num_predict": settings.llm_max_tokens,
            },
        )

        for chunk in stream:
            token = chunk.get("message", {}).get("content", "")
            if token:
                yield token

    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        raise


def chat(
    prompt: str,
    system_prompt: str | None = None,
) -> str:
    """Generate a complete (non-streaming) response."""
    sys_prompt = system_prompt or CLINICAL_SYSTEM_PROMPT

    try:
        response = ollama.chat(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            options={
                "temperature": settings.llm_temperature,
                "top_k": settings.llm_top_k,
                "num_predict": settings.llm_max_tokens,
            },
        )
        return response["message"]["content"]
    except Exception as e:
        logger.error(f"LLM inference failed: {e}")
        raise


def check_ollama_status() -> dict:
    """Check if Ollama is running and the required models are available."""
    try:
        models = ollama.list()
        model_names = [m.get("name", "") for m in models.get("models", [])]

        llm_ready = any(settings.llm_model in n for n in model_names)
        embed_ready = any(settings.embedding_model in n for n in model_names)

        return {
            "ollama_running": True,
            "llm_model_ready": llm_ready,
            "embedding_model_ready": embed_ready,
            "llm_model": settings.llm_model,
            "embedding_model": settings.embedding_model,
            "available_models": model_names,
        }
    except Exception as e:
        return {
            "ollama_running": False,
            "error": str(e),
        }
