"""PhysioWave — RAG Pipeline Orchestrator.

Three-step pipeline:
1. Parse — Extract text from PDFs via PyMuPDF
2. Embed — Generate 768-dim vectors via Ollama nomic-embed-text
3. Store — Index in ChromaDB with HNSW cosine similarity

Also handles semantic search for the retrieval pass.
"""

import uuid
import typing

from backend.core.config import settings
from backend.core.logger import logger
from backend.rag.embeddings import embed_document, embed_query, embed_texts
from backend.rag.pdf_parser import extract_and_chunk
from backend.rag.vector_store import add_documents, get_document_count, search


# ─── Ingestion ────────────────────────────────────────────────────────

def ingest_document(
    file_path: str,
    document_type: str,
    job_id: int | None = None,
    check_cancelled: typing.Callable[[], bool] | None = None,
    extract_images: bool = True,
    safe_mode: bool = False,
) -> int:
    """Ingest a single PDF: parse → embed → store.

    Supports crash recovery and real-time DB progress updates.
    Returns the number of chunks ingested.
    """
    import sqlite3
    db_path = settings.database_url.replace("sqlite:///", "")

    def update_progress(ingested_count: int, total_count: int | None = None):
        if not job_id: return
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            if total_count is not None:
                cur.execute("UPDATE ingestion_status SET total_chunks = ?, ingested_chunks = ? WHERE id = ?", (total_count, ingested_count, job_id))
            else:
                cur.execute("UPDATE ingestion_status SET ingested_chunks = ? WHERE id = ?", (ingested_count, job_id))
            conn.commit()
        finally:
            conn.close()

    def update_status(status: str):
        if not job_id: return
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute("UPDATE ingestion_status SET status = ? WHERE id = ?", (status, job_id))
            conn.commit()
        finally:
            conn.close()


    # Step 1: Parse (with crash-resumable chunk cache)
    import os
    import json
    from backend.rag.pdf_parser import DocumentChunk
    
    cache_dir = os.path.join(settings.upload_dir, ".chunk_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"job_{job_id}.json") if job_id else None
    
    # Check for existing parse cache from a previous interrupted run
    cached_chunks: list[DocumentChunk] = []
    resume_page = 0
    
    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, "r") as f:
                cache_data = json.load(f)
            resume_page = cache_data.get("last_page", 0)
            cached_chunks = [
                DocumentChunk(**c) for c in cache_data.get("chunks", [])
            ]
            logger.info(f"Loaded parse cache: {len(cached_chunks)} chunks from {resume_page} pages")
        except Exception as e:
            logger.warning(f"Failed to load parse cache, starting fresh: {e}")
            cached_chunks = []
            resume_page = 0

    update_status("parsing")
    
    # Get total page count early for UI visibility during parsing
    try:
        import fitz
        doc_meta = fitz.open(file_path)
        total_pages = len(doc_meta)
        doc_meta.close()
        update_progress(resume_page, total_pages)
    except Exception:
        total_pages = 0

    def on_parsing_progress(current: int, total: int):
        update_progress(current, total)

    def on_page_complete(last_page: int, chunks_so_far: list):
        """Save chunks to disk cache so parsing can resume after a crash."""
        if not cache_path:
            return
        try:
            cache_data = {
                "last_page": last_page,
                "chunks": [
                    {
                        "text": c.text,
                        "source_file": c.source_file,
                        "page_number": c.page_number,
                        "chunk_index": c.chunk_index,
                        "document_type": c.document_type,
                    }
                    for c in chunks_so_far
                ],
            }
            with open(cache_path, "w") as f:
                json.dump(cache_data, f)
        except Exception as e:
            logger.warning(f"Failed to save parse cache: {e}")

    chunks = extract_and_chunk(
        file_path, 
        document_type=document_type, 
        extract_images=extract_images,
        on_progress=on_parsing_progress,
        check_cancelled=check_cancelled,
        start_page=resume_page,
        existing_chunks=cached_chunks,
        on_page_complete=on_page_complete,
    )
    if not chunks:
        update_progress(0, 0)
        if not extract_images:
            raise ValueError("0 chunks extracted. If this is a scanned document, please enable the Extract Images toggle.")
        else:
            raise ValueError("No text or recognizable content could be extracted from this PDF.")

    # Check if cancelled during parsing before proceeding to embedding
    if check_cancelled and check_cancelled():
        logger.warning(f"Cancelled after parsing. Not proceeding to embedding.")
        return 0

    total = len(chunks)
    logger.info(f"Embedding {total} chunks from {file_path}")
    
    # Parsing is complete — delete the chunk cache (no longer needed)
    if cache_path and os.path.exists(cache_path):
        try:
            os.remove(cache_path)
            logger.info("Parse cache deleted (parsing complete).")
        except Exception:
            pass
    
    # Step 2: Transition to Processing (Embedding)
    update_status("processing")

    # ── Smart Resume Logic ─────────────────────────────────────────
    # During parsing, `total_chunks` held the page count (e.g., 345).
    # During embedding, `total_chunks` holds the chunk count (e.g., 500).
    # If the stored total_chunks MATCHES our current chunk count, a previous
    # run made it to the embedding phase — we can safely resume from
    # `ingested_chunks`. Otherwise, start fresh.
    ingested = 0
    if job_id:
        conn = sqlite3.connect(db_path)
        try:
            cur = conn.cursor()
            cur.execute("SELECT ingested_chunks, total_chunks FROM ingestion_status WHERE id = ?", (job_id,))
            row = cur.fetchone()
            stored_ingested = row[0] if row and row[0] else 0
            stored_total = row[1] if row and row[1] else 0
        finally:
            conn.close()
        
        if stored_total == total and stored_ingested > 0:
            ingested = stored_ingested
            logger.info(f"Crash recovery: Resuming embedding from chunk {ingested}/{total}")
        else:
            logger.info(f"Fresh embedding start (stored_total={stored_total}, actual_total={total})")

    update_progress(ingested, total)

    # Step 2 & 3: Embed and store in batches
    batch_size = 1 if safe_mode else 5  # Safe mode reduces VRAM spikes
    
    if safe_mode:
        logger.info(f"Safe Mode active for Job {job_id}: Processing with batch_size=1")

    for i in range(ingested, total, batch_size):
        if check_cancelled and check_cancelled():
            logger.warning(f"Ingestion cancelled for {file_path}. Aborting thread.")
            return ingested

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
        update_progress(ingested)

    logger.info(f"Ingested {ingested} chunks from {file_path}")
    return ingested



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
