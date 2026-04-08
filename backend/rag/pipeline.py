"""PhysioWave — RAG Pipeline Orchestrator.

Three-step pipeline:
1. Parse — Extract text from PDFs via PyMuPDF
2. Embed — Generate 768-dim vectors via Ollama nomic-embed-text
3. Store — Index in ChromaDB with HNSW cosine similarity

Also handles semantic search for the retrieval pass.
"""

import uuid

from backend.core.config import settings
from backend.core.logger import logger
from backend.rag.embeddings import embed_document, embed_query, embed_texts
from backend.rag.pdf_parser import (
    DocumentChunk,
    extract_and_chunk,
    get_all_pdf_paths,
)
from backend.rag.vector_store import add_documents, get_document_count, search


# ─── Ingestion ────────────────────────────────────────────────────────

def ingest_document(
    file_path: str,
    document_type: str,
    on_progress: callable | None = None,
) -> int:
    """Ingest a single PDF: parse → embed → store.

    Returns the number of chunks ingested.
    """
    # Step 1: Parse
    chunks = extract_and_chunk(file_path, document_type=document_type)
    if not chunks:
        logger.warning(f"No text extracted from {file_path}")
        return 0

    total = len(chunks)
    logger.info(f"Embedding {total} chunks from {file_path}")

    # Step 2 & 3: Embed and store in batches
    batch_size = 20
    ingested = 0

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]

        # Generate embeddings for the batch
        texts = [c.text for c in batch]
        embeddings = embed_texts(texts)

        # Prepare for ChromaDB
        ids = [str(uuid.uuid4()) for _ in batch]
        metadatas = [
            {
                "source_file": c.source_file,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index,
                "document_type": c.document_type,
            }
            for c in batch
        ]

        add_documents(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        ingested += len(batch)
        if on_progress:
            on_progress(ingested, total)

    logger.info(f"Ingested {ingested} chunks from {file_path}")
    return ingested


def ingest_all_documents(
    on_progress: callable | None = None,
) -> dict:
    """Ingest all PDF assets.

    Returns summary: {total_chunks, documents_processed, errors}.
    """
    assets = get_all_pdf_paths()
    total_chunks = 0
    errors: list[str] = []

    for i, asset in enumerate(assets):
        if on_progress:
            on_progress(i, len(assets), asset["display_name"])

        try:
            count = ingest_document(
                file_path=asset["path"],
                document_type=asset["document_type"],
            )
            total_chunks += count
        except Exception as e:
            error_msg = f"Failed to ingest {asset['display_name']}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    if on_progress:
        on_progress(len(assets), len(assets), None)

    logger.info(
        f"Ingestion complete: {total_chunks} chunks from "
        f"{len(assets)} documents ({len(errors)} errors)"
    )

    return {
        "total_chunks": total_chunks,
        "documents_processed": len(assets),
        "errors": errors,
    }


# ─── Search ───────────────────────────────────────────────────────────

def semantic_search(
    query: str,
    top_k: int | None = None,
    document_type: str | None = None,
) -> list[dict]:
    """Perform semantic search against the clinical knowledge base.

    Args:
        query: Natural language search query.
        top_k: Max results (default from settings).
        document_type: Filter by type ('clinical_guide', 'equipment_manual').

    Returns:
        List of search results with content, score, and metadata.
    """
    k = top_k or settings.search_top_k

    # Embed the query
    query_emb = embed_query(query)

    # Build filter
    where = None
    if document_type:
        where = {"document_type": document_type}

    # Search
    results = search(query_emb, top_k=k, where=where)

    # Format results
    formatted: list[dict] = []
    if results["documents"] and results["documents"][0]:
        for j in range(len(results["documents"][0])):
            distance = results["distances"][0][j] if results["distances"] else 1.0
            score = 1.0 - distance  # Convert distance to similarity

            if score < settings.search_threshold:
                continue

            formatted.append({
                "content": results["documents"][0][j],
                "score": round(score, 4),
                "source_file": results["metadatas"][0][j].get("source_file", ""),
                "page_number": results["metadatas"][0][j].get("page_number"),
                "document_type": results["metadatas"][0][j].get("document_type", ""),
            })

    logger.info(f"Semantic search for '{query[:50]}...': {len(formatted)} results")
    return formatted
