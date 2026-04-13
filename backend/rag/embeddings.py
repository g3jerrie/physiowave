"""PhysioWave — Embedding Service.

Wraps Ollama's /api/embed endpoint for generating text embeddings
using the nomic-embed-text model (768-dimensional vectors).
"""

import ollama

from backend.core.config import settings
from backend.core.logger import logger


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts.

    Uses Ollama's /api/embed endpoint with the configured embedding model.
    Returns a list of 768-dimensional vector embeddings.
    """
    if not texts:
        return []

    try:
        # Pass timeout to prevent GPU OOM or CPU fallback errors from failing too fast
        # Note: Ollama python client sets timeout via Client(timeout) or passing options
        client = ollama.Client(host=settings.ollama_base_url, timeout=300.0)
        response = client.embed(
            model=settings.embedding_model,
            input=texts,
        )
        return response["embeddings"]
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise


def embed_query(query: str) -> list[float]:
    """Generate embedding for a single search query."""
    embeddings = embed_texts([query])
    if not embeddings:
        raise ValueError("No embedding returned for query")
    return embeddings[0]


def embed_document(text: str) -> list[float]:
    """Generate embedding for a document chunk."""
    embeddings = embed_texts([text])
    if not embeddings:
        raise ValueError("No embedding returned for document")
    return embeddings[0]

def extract_image_description(base64_image: str) -> str:
    """Generate a textual description for an extracted image using Vision model."""
    try:
        client = ollama.Client(host=settings.ollama_base_url, timeout=300.0)
        response = client.chat(
            model=settings.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": "You are a clinical AI assistant. Describe this medical or equipment diagram in high detail, focusing on textual data, components, relationships, and actionable knowledge. Do not start with 'This is an image of', just describe the contents directly.",
                    "images": [base64_image]
                }
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        logger.error(f"Vision model failed to describe image: {e}")
        return ""
