"""PhysioWave — RAG Management Router."""

import os
from datetime import datetime, timezone
import json
import asyncio
import hashlib
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.core.config import settings
from backend.core.logger import logger
from backend.core.database import get_db
from backend.models.schemas import SearchRequest, SearchResultItem
from backend.rag.pipeline import semantic_search
from backend.rag.vector_store import get_document_count

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form("clinical_guide"),
    extract_images: str = Form("true"),
    force: bool = Form(False),
):
    """Upload a PDF document to the Knowledge Base (Queue)."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    db = await get_db()
    try:
        # Duplicate detection
        if not force:
            cursor = await db.execute(
                "SELECT id, status FROM ingestion_status WHERE filename = ? AND status NOT IN ('failed', 'cancelled')",
                (file.filename,)
            )
            row = await cursor.fetchone()
            if row:
                existing = dict(row)
                raise HTTPException(
                    status_code=409, 
                    detail=f"File '{file.filename}' is already {existing['status']}. Use force=true to re-upload."
                )

        os.makedirs(settings.upload_dir, exist_ok=True)
        file_path = os.path.join(settings.upload_dir, file.filename)
        
        with open(file_path, "wb") as f:
            f.write(await file.read())

        created_at = datetime.now(timezone.utc).isoformat()
        do_extract = 1 if extract_images.lower() == "true" else 0
        
        cursor = await db.execute(
            "INSERT INTO ingestion_status (filename, extract_images, status, created_at) VALUES (?, ?, ?, ?)",
            (file.filename, do_extract, "pending", created_at)
        )
        await db.commit()
        ingestion_id = cursor.lastrowid
    finally:
        await db.close()

    return {
        "status": "upload_success",
        "ingestion_id": ingestion_id,
        "message": "File uploaded and placed in queue.",
    }


@router.get("/uploads")
async def list_uploads():
    """Get the statuses of all uploaded documents."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ingestion_status ORDER BY id DESC")
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        await db.close()


@router.get("/uploads/stream")
async def stream_uploads(request: Request):
    """SSE push stream for real-time upload status updates.
    
    Architecture:
    - Single persistent connection per browser tab
    - Server polls DB internally every 2s (not the browser)
    - Only pushes data when state actually changes (hash-diffed)
    - Sends keepalive comments to prevent connection timeouts
    """
    async def event_generator():
        last_state_hash = None
        while True:
            # Check if client disconnected
            try:
                if await request.is_disconnected():
                    logger.info("SSE client disconnected.")
                    break
            except Exception:
                break

            # Read current state from DB
            try:
                db = await get_db()
                try:
                    cursor = await db.execute("SELECT * FROM ingestion_status ORDER BY id DESC")
                    rows = await cursor.fetchall()
                    uploads = [dict(row) for row in rows]
                finally:
                    await db.close()

                data = json.dumps(uploads, default=str)
                current_hash = hashlib.md5(data.encode()).hexdigest()

                if current_hash != last_state_hash:
                    yield f"data: {data}\n\n"
                    last_state_hash = current_hash
                else:
                    # Keepalive: send SSE comment to prevent connection timeout
                    yield ": heartbeat\n\n"
            except Exception as e:
                logger.warning(f"SSE generator DB error: {e}")
                yield ": heartbeat\n\n"

            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )



@router.delete("/uploads/{upload_id}")
async def delete_upload(upload_id: int, purge_vectors: bool = False):
    """Delete an upload, its file, and optionally its vectors."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ingestion_status WHERE id = ?", (upload_id,))
        row_obj = await cursor.fetchone()
        if not row_obj:
            raise HTTPException(status_code=404, detail="Upload not found")
        row = dict(row_obj)
        
        # 1. Update status to cancelled so the worker drops it if processing
        await db.execute("UPDATE ingestion_status SET status = 'cancelled' WHERE id = ?", (upload_id,))
        await db.commit()
        
        # 2. Delete file if it exists
        if row["filename"]:
            file_path = os.path.join(settings.upload_dir, row["filename"])
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        # 3. Optionally delete from vector store
        if purge_vectors:
            from backend.rag.vector_store import get_collection
            try:
                collection = get_collection()
                collection.delete(where={"source_file": row["filename"]})
                logger.info(f"Deleted vectors for {row['filename']}")
            except Exception as e:
                logger.error(f"Failed to delete vectors: {e}")
        else:
            logger.info(f"Skipped purging vectors for {row['filename']}")
            
        # 4. Remove from database entirely
        await db.execute("DELETE FROM ingestion_status WHERE id = ?", (upload_id,))
        await db.commit()

        return {"status": "deleted", "purged_vectors": purge_vectors}
    finally:
        await db.close()


@router.post("/uploads/{upload_id}/retry")
async def retry_upload(
    upload_id: int,
    extract_images: bool | None = None,
    safe_mode: bool | None = None
):
    """Retry a failed ingestion task with optional flag overrides."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT * FROM ingestion_status WHERE id = ?", (upload_id,))
        row_obj = await cursor.fetchone()
        if not row_obj:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        row = dict(row_obj)
        
        if row["status"] not in ("failed", "cancelled"):
            raise HTTPException(status_code=400, detail="Only failed or cancelled uploads can be retried.")

        file_path = os.path.join(settings.upload_dir, row["filename"])
        if not os.path.exists(file_path):
             raise HTTPException(status_code=404, detail="Original pdf not found on disk. Please re-upload.")

        # Build update query
        updates = ["status = 'pending'", "error_message = NULL", "ingested_chunks = 0"]
        params = []
        if extract_images is not None:
            updates.append("extract_images = ?")
            params.append(1 if extract_images else 0)
        if safe_mode is not None:
            updates.append("safe_mode = ?")
            params.append(1 if safe_mode else 0)
        
        params.append(upload_id)
        query = f"UPDATE ingestion_status SET {', '.join(updates)} WHERE id = ?"
        
        await db.execute(query, params)
        await db.commit()
        return {"status": "retry_started", "ingestion_id": upload_id}
    finally:
        await db.close()


@router.post("/search", response_model=list[SearchResultItem])
async def search_knowledge_base(request: SearchRequest):
    """Perform semantic search against the clinical knowledge base."""
    results = semantic_search(
        query=request.query,
        top_k=request.top_k,
        document_type=request.document_type,
    )

    return [
        SearchResultItem(
            content=r["content"],
            score=r["score"],
            source_file=r["source_file"],
            page_number=r.get("page_number"),
            document_type=r.get("document_type"),
        )
        for r in results
    ]


@router.get("/status")
async def rag_status():
    """Get RAG pipeline status."""
    count = get_document_count()
    return {
        "total_chunks": count,
        "is_ingested": count > 0,
    }
