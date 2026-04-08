"""PhysioWave — ChromaDB Vector Store.

HIPAA Compliance Note: All vector data is stored locally on-device in
ChromaDB's persistent storage directory. No data is transmitted externally.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.core.config import settings
from backend.core.logger import logger

# ─── ChromaDB Client ─────────────────────────────────────────────────

_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "physiowave_clinical"


def get_client() -> chromadb.PersistentClient:
    """Get or create the ChromaDB persistent client."""
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chromadb_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info(f"ChromaDB initialized at: {settings.chromadb_path}")
    return _client


def get_collection() -> chromadb.Collection:
    """Get or create the clinical documents collection."""
    global _collection
    if _collection is None:
        client = get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"Collection '{COLLECTION_NAME}' ready "
            f"({_collection.count()} documents)"
        )
    return _collection


def add_documents(
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    """Add documents with their embeddings to the vector store."""
    collection = get_collection()
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def search(
    query_embedding: list[float],
    top_k: int = 10,
    where: dict | None = None,
) -> dict:
    """Search for similar documents by embedding vector.

    Returns ChromaDB results dict with: ids, documents, metadatas, distances.
    """
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return results


def get_document_count() -> int:
    """Return total number of documents in the collection."""
    return get_collection().count()


def reset_collection() -> None:
    """Delete and recreate the collection. Use with caution."""
    global _collection
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    _collection = None
    get_collection()
    logger.info("Vector store reset")
