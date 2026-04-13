"""PhysioWave — Application Configuration.

Loads settings from environment variables / .env file.
All configuration is centralized here for easy auditing.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # ─── Ollama (Local AI Server) ──────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "gemma3:4b"
    vision_model: str = "moondream"
    embedding_model: str = "nomic-embed-text"

    # ─── LLM Inference ─────────────────────────────────────────────────
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_top_k: int = 40

    # ─── RAG Pipeline ──────────────────────────────────────────────────
    chunk_size: int = 1500  # Characters per chunk
    chunk_overlap: int = 200  # Overlap between consecutive chunks
    search_top_k: int = 10  # Max results from vector search
    search_threshold: float = 0.6  # Min similarity score (0.0-1.0)

    # ─── Database ──────────────────────────────────────────────────────
    database_url: str = "sqlite:///./backend/data/physiowave.db"
    chromadb_path: str = "./backend/data/chromadb"

    # ─── Security ──────────────────────────────────────────────────────
    # HIPAA Compliance Note: encryption_key protects PII at rest.
    # Generate via: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = ""
    secret_key: str = ""

    # ─── Server ────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # ─── Assets ────────────────────────────────────────────────────────
    assets_dir: str = "./backend/assets"
    upload_dir: str = "./backend/data/uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
